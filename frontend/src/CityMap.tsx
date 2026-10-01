import {useEffect,useRef,useState,useLayoutEffect} from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import type {GeoJSONSource,ExpressionSpecification} from 'maplibre-gl';
import type {GeoData,District,Metric} from './types';
import {format} from './types';
import 'maplibre-gl/dist/maplibre-gl.css';
maplibregl.setWorkerUrl(workerUrl);

const colors=['#afcfb7','#85b69d','#50977b','#27775d','#104d3d'];
const bangkokBounds:maplibregl.LngLatBoundsLike=[[100.32,13.48],[100.97,13.96]];
const motionDuration=()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches?0:450;
// Thai labels are rasterized locally at 2x then collision-placed by a symbol layer.
// This avoids a remote glyph server and preserves Thai shaping via the browser.
function labelImage(name:string){
 const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d')!;
 ctx.font='600 26px Tahoma, sans-serif';canvas.width=Math.ceil(ctx.measureText(name).width)+16;canvas.height=50;
 ctx.font='600 26px Tahoma, sans-serif';ctx.textBaseline='middle';ctx.lineJoin='round';ctx.lineWidth=6;ctx.strokeStyle='#fff';ctx.strokeText(name,8,25);ctx.fillStyle='#173c32';ctx.fillText(name,8,25);
 return ctx.getImageData(0,0,canvas.width,canvas.height);
}
export function CityMap({geometry,rows,metric,selected,onSelect,points,focusSelected=true}:{geometry:GeoData;rows:District[];metric:Metric;selected?:string;onSelect:(id:string)=>void;points?:GeoData|null;focusSelected?:boolean}){
 const container=useRef<HTMLDivElement>(null),mapRef=useRef<maplibregl.Map|null>(null);
 const latest=useRef({rows,metric,onSelect});latest.current={rows,metric,onSelect};
 const [ready,setReady]=useState(false),[error,setError]=useState(''),[hover,setHover]=useState<{row:District;x:number;y:number}|null>(null);
 const tooltipRef=useRef<HTMLDivElement>(null);const [tooltipPosition,setTooltipPosition]=useState({left:0,top:0});
 const [contextError,setContextError]=useState(false);
 useLayoutEffect(()=>{if(!hover||!container.current||!tooltipRef.current)return;const w=container.current.clientWidth,h=container.current.clientHeight;const box=tooltipRef.current.getBoundingClientRect();setTooltipPosition({left:Math.max(8,Math.min(hover.x+16,w-box.width-8)),top:Math.max(8,hover.y+18+box.height<h?hover.y+18:hover.y-box.height-12)});},[hover,metric]);
 useEffect(()=>{const dismiss=(event:KeyboardEvent)=>{if(event.key==='Escape')setHover(null);};window.addEventListener('keydown',dismiss);return()=>window.removeEventListener('keydown',dismiss);},[]);
 const values=rows.map(r=>r[metric.id]).filter((v):v is number=>v!=null), max=Math.max(...values,1);
 const mean=values.length?values.reduce((sum,v)=>sum+v,0)/values.length:null;
 const difference=hover&&mean!==null&&hover.row[metric.id]!==null?hover.row[metric.id]!-mean:null;
 useEffect(()=>{
  if(!container.current)return;
  let map:maplibregl.Map;
  try{map=new maplibregl.Map({container:container.current,style:{version:8,sources:{},layers:[{id:'background',type:'background',paint:{'background-color':'#f1f3ed'}}]},center:[100.62,13.78],zoom:9.5,attributionControl:false});}
  catch{setError('อุปกรณ์นี้ไม่รองรับแผนที่ WebGL ใช้ตารางรายเขตด้านล่างแทนได้');return;}
  mapRef.current=map;
  map.on('movestart',()=>{setHover(null);if(container.current)delete container.current.dataset.renderedDistricts;});
  map.on('error',e=>{if('sourceId' in e&&e.sourceId==='river'){setContextError(true);return;}setError('โหลดแผนที่ไม่สำเร็จ กรุณาโหลดหน้าใหม่ หรือใช้ตารางรายเขต');});
  map.on('idle',()=>{if(container.current&&map.getLayer('district-fill')){container.current.dataset.renderedDistricts=String(new Set(map.queryRenderedFeatures({layers:['district-fill']}).map(f=>f.properties?.district_code)).size);container.current.dataset.renderedLabels=String(map.queryRenderedFeatures({layers:['district-labels']}).length);container.current.dataset.renderedRiver=String(map.queryRenderedFeatures({layers:['river-line']}).length);container.current.dataset.zoom=String(map.getZoom());}});
  map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
  map.addControl(new maplibregl.AttributionControl({compact:true,customAttribution:'ขอบเขต © กรุงเทพมหานคร | แนวแม่น้ำและพิกัดสถานีบางส่วน © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'}),'bottom-right');
  map.on('load',()=>{
   map.addSource('districts',{type:'geojson',data:geometry,promoteId:'district_code'});
   map.addLayer({id:'district-fill',type:'fill',source:'districts',paint:{'fill-color':'#7db395','fill-opacity':0.93}});
   map.addSource('river',{type:'geojson',data:'/context/chao-phraya.geojson'});
   map.addLayer({id:'river-casing',type:'line',source:'river',paint:{'line-color':'#effaff','line-width':['interpolate',['linear'],['zoom'],8,3,13,9]}});
   map.addLayer({id:'river-line',type:'line',source:'river',paint:{'line-color':'#287eae','line-width':['interpolate',['linear'],['zoom'],8,1.5,13,5]}});
   map.addLayer({id:'district-line',type:'line',source:'districts',paint:{'line-color':'#fff','line-width':1.2}});
   map.addLayer({id:'selected-line',type:'line',source:'districts',filter:['==',['get','district_code'],''],paint:{'line-color':'#173e34','line-width':3}});
   map.addSource('points',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
   map.addLayer({id:'point-circles',type:'circle',source:'points',paint:{'circle-radius':4,'circle-color':'#dd6b3e','circle-stroke-color':'#fff','circle-stroke-width':1.3}});
   const labels:GeoData={type:'FeatureCollection',features:geometry.features.filter(f=>f.properties?.label_point).map(f=>({type:'Feature',geometry:f.properties!.label_point,properties:f.properties}))};
   for(const f of labels.features){map.addImage('name-'+f.properties!.district_code,labelImage(f.properties!.name_th),{pixelRatio:2});}
   map.addSource('district-labels',{type:'geojson',data:labels});
   map.addLayer({id:'district-labels',type:'symbol',source:'district-labels',minzoom:9,layout:{'icon-image':['concat','name-',['get','district_code']],'icon-allow-overlap':false,'icon-padding':5,'icon-size':['interpolate',['linear'],['zoom'],9,0.9,12,1.1]}});
   setReady(true);map.fitBounds([[100.32,13.48],[100.97,13.96]],{padding:30,duration:0});
  });
  map.on('mousemove','district-fill',e=>{const code=e.features?.[0]?.properties?.district_code;const row=latest.current.rows.find(r=>r.district_code===code);setHover(row?{row,x:e.point.x,y:e.point.y}:null);map.getCanvas().style.cursor='pointer';});
  map.on('mouseleave','district-fill',()=>{setHover(null);map.getCanvas().style.cursor='';});
  map.on('click','district-fill',e=>{setHover(null);const code=e.features?.[0]?.properties?.district_code;if(code)latest.current.onSelect(code);});
  map.on('click','point-circles',e=>{const f=e.features?.[0];if(!f)return;const node=document.createElement('div');node.textContent=f.properties?.name;new maplibregl.Popup().setLngLat(e.lngLat).setDOMContent(node).addTo(map);});
  const resize=new ResizeObserver(()=>map.resize());resize.observe(container.current);
  return()=>{resize.disconnect();map.remove();mapRef.current=null;};
 },[geometry]);
 useEffect(()=>{const map=mapRef.current;if(!ready||!map)return;
  const mapped={...geometry,features:geometry.features.map(f=>({...f,properties:{...f.properties,value:rows.find(r=>r.district_code===f.properties?.district_code)?.[metric.id]??null}}))};
  (map.getSource('districts') as GeoJSONSource).setData(mapped);
  const expression:ExpressionSpecification=['case',['==',['get','value'],null],'#d8d8df',['interpolate',['linear'],['get','value'],0,colors[0],max*.25,colors[1],max*.5,colors[2],max*.75,colors[3],max,colors[4]]];
  map.setPaintProperty('district-fill','fill-color',expression);
  map.setFilter('selected-line',['==',['get','district_code'],selected||'']);
  (map.getSource('points') as GeoJSONSource).setData(points||{type:'FeatureCollection',features:[]});
 },[ready,geometry,rows,metric,max,selected,points]);
 useEffect(()=>{const map=mapRef.current;if(!ready||!map||!focusSelected)return;
  const f=geometry.features.find(f=>f.properties?.district_code===selected);
  if(!f||f.geometry.type==='GeometryCollection'){map.fitBounds([[100.32,13.48],[100.97,13.96]],{padding:35,duration:motionDuration()});return;}
  const bounds=new maplibregl.LngLatBounds();
  function walk(coords:unknown){if(!Array.isArray(coords))return;if(typeof coords[0]==='number'){bounds.extend([coords[0],coords[1] as number]);}else coords.forEach(walk);}
  walk(f.geometry.coordinates);map.fitBounds(bounds,{padding:60,maxZoom:13,duration:motionDuration()});
 },[selected,ready,geometry,focusSelected]);
 return <div className="map-shell"><div className="map" ref={container} role="region" aria-label="แผนที่ 50 เขตกรุงเทพมหานคร"/>
  <div className="map-tag"><span className="live-dot"/> BANGKOK <span>13.7563° N · 100.5018° E</span></div>
  {error&&<div role="alert" className="map-error">{error}</div>}
  {hover&&<div ref={tooltipRef} role="tooltip" className="map-hover" style={tooltipPosition}><small>{hover.row.name_en}</small><strong>{hover.row.name_th}</strong><span>{format(hover.row[metric.id],metric.decimals)} <small>{metric.unit}</small></span><p>ค่าเฉลี่ยรายเขต {format(mean,metric.decimals)} {metric.unit}</p><p>{difference===null?'ไม่มีข้อมูลเปรียบเทียบ':difference===0?'เท่ากับค่าเฉลี่ย':`${difference>0?'สูงกว่า':'ต่ำกว่า'}เฉลี่ย ${format(Math.abs(difference),metric.decimals)} ${metric.unit}`}</p><small>ไม่ถ่วงน้ำหนัก · {values.length} เขตที่มีข้อมูล</small></div>}
  <button className="map-reset" onClick={()=>{setHover(null);mapRef.current?.fitBounds(bangkokBounds,{padding:35,duration:motionDuration()});}}>ดูครบ 50 เขต</button>
  {contextError&&<div className="map-context-warning" role="status">โหลดแนวแม่น้ำไม่สำเร็จ</div>}
  <div className="map-legend"><strong>{metric.label}</strong><div className="gradient"/><div className="legend-values"><span>0</span><span>{format(max,metric.decimals)} {metric.unit}</span></div><small>สีเข้ม = ค่ามาก · คลิกเขตเพื่อดูรายละเอียด</small><div className="legend-context"><span><i className="missing-swatch"/> ไม่มีข้อมูล</span><span><i className="river-swatch"/> เจ้าพระยา</span></div></div>
  <div className="north">N<span>↑</span></div>
 </div>;
}
