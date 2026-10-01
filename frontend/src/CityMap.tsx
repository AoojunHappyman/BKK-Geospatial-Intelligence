import {useEffect,useRef,useState} from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import type {GeoJSONSource,ExpressionSpecification} from 'maplibre-gl';
import type {GeoData,District,Metric} from './types';
import {format} from './types';
import 'maplibre-gl/dist/maplibre-gl.css';
maplibregl.setWorkerUrl(workerUrl);

const colors=['#e2eee4','#b8d4bc','#7db395','#408d73','#155e4e'];
export function CityMap({geometry,rows,metric,selected,onSelect,points,focusSelected=true}:{geometry:GeoData;rows:District[];metric:Metric;selected?:string;onSelect:(id:string)=>void;points?:GeoData|null;focusSelected?:boolean}){
 const container=useRef<HTMLDivElement>(null),mapRef=useRef<maplibregl.Map|null>(null);
 const latest=useRef({rows,metric,onSelect});latest.current={rows,metric,onSelect};
 const [ready,setReady]=useState(false),[error,setError]=useState(''),[hover,setHover]=useState<District|null>(null);
 const values=rows.map(r=>r[metric.id]).filter((v):v is number=>v!=null), max=Math.max(...values,1);
 useEffect(()=>{
  if(!container.current)return;
  let map:maplibregl.Map;
  try{map=new maplibregl.Map({container:container.current,style:{version:8,sources:{},layers:[{id:'background',type:'background',paint:{'background-color':'#edf0e9'}}]},center:[100.62,13.78],zoom:9.5,attributionControl:false});}
  catch{setError('อุปกรณ์นี้ไม่รองรับแผนที่ WebGL ใช้ตารางรายเขตด้านล่างแทนได้');return;}
  mapRef.current=map;
  map.on('movestart',()=>{if(container.current)delete container.current.dataset.renderedDistricts;});
  map.on('error',()=>setError('โหลดแผนที่ไม่สำเร็จ กรุณาโหลดหน้าใหม่ หรือใช้ตารางรายเขต'));
  map.on('idle',()=>{if(container.current&&map.getLayer('district-fill'))container.current.dataset.renderedDistricts=String(new Set(map.queryRenderedFeatures({layers:['district-fill']}).map(f=>f.properties?.district_code)).size);});
  map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
  map.addControl(new maplibregl.AttributionControl({compact:true,customAttribution:'ขอบเขต © กรุงเทพมหานคร | พิกัดสถานีบางส่วน © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'}),'bottom-right');
  map.on('load',()=>{
   map.addSource('districts',{type:'geojson',data:geometry,promoteId:'district_code'});
   map.addLayer({id:'district-fill',type:'fill',source:'districts',paint:{'fill-color':'#7db395','fill-opacity':0.93}});
   map.addLayer({id:'district-line',type:'line',source:'districts',paint:{'line-color':'#fff','line-width':1.2}});
   map.addLayer({id:'selected-line',type:'line',source:'districts',filter:['==',['get','district_code'],''],paint:{'line-color':'#173e34','line-width':3}});
   map.addSource('points',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
   map.addLayer({id:'point-circles',type:'circle',source:'points',paint:{'circle-radius':4,'circle-color':'#dd6b3e','circle-stroke-color':'#fff','circle-stroke-width':1.3}});
   setReady(true);map.fitBounds([[100.32,13.48],[100.97,13.96]],{padding:30,duration:0});
  });
  map.on('mousemove','district-fill',e=>{const code=e.features?.[0]?.properties?.district_code;setHover(latest.current.rows.find(r=>r.district_code===code)||null);map.getCanvas().style.cursor='pointer';});
  map.on('mouseleave','district-fill',()=>{setHover(null);map.getCanvas().style.cursor='';});
  map.on('click','district-fill',e=>{const code=e.features?.[0]?.properties?.district_code;if(code)latest.current.onSelect(code);});
  map.on('click','point-circles',e=>{const f=e.features?.[0];if(!f)return;const node=document.createElement('div');node.textContent=f.properties?.name;new maplibregl.Popup().setLngLat(e.lngLat).setDOMContent(node).addTo(map);});
  return()=>{map.remove();mapRef.current=null;};
 },[geometry]);
 useEffect(()=>{const map=mapRef.current;if(!ready||!map)return;
  const mapped={...geometry,features:geometry.features.map(f=>({...f,properties:{...f.properties,value:rows.find(r=>r.district_code===f.properties?.district_code)?.[metric.id]??null}}))};
  (map.getSource('districts') as GeoJSONSource).setData(mapped);
  const expression:ExpressionSpecification=['case',['==',['get','value'],null],'#c3c8c3',['interpolate',['linear'],['get','value'],0,colors[0],max*.25,colors[1],max*.5,colors[2],max*.75,colors[3],max,colors[4]]];
  map.setPaintProperty('district-fill','fill-color',expression);
  map.setFilter('selected-line',['==',['get','district_code'],selected||'']);
  (map.getSource('points') as GeoJSONSource).setData(points||{type:'FeatureCollection',features:[]});
 },[ready,geometry,rows,metric,max,selected,points]);
 useEffect(()=>{const map=mapRef.current;if(!ready||!map||!focusSelected)return;
  const f=geometry.features.find(f=>f.properties?.district_code===selected);
  if(!f||f.geometry.type==='GeometryCollection'){map.fitBounds([[100.32,13.48],[100.97,13.96]],{padding:35,duration:500});return;}
  const bounds=new maplibregl.LngLatBounds();
  function walk(coords:unknown){if(!Array.isArray(coords))return;if(typeof coords[0]==='number'){bounds.extend([coords[0],coords[1] as number]);}else coords.forEach(walk);}
  walk(f.geometry.coordinates);map.fitBounds(bounds,{padding:60,maxZoom:13,duration:600});
 },[selected,ready,geometry,focusSelected]);
 return <div className="map-shell"><div className="map" ref={container} role="region" aria-label="แผนที่ 50 เขตกรุงเทพมหานคร"/>
  <div className="map-tag"><span className="live-dot"/> BANGKOK <span>13.7563° N · 100.5018° E</span></div>
  {error&&<div role="alert" className="map-error">{error}</div>}
  {hover&&<div className="map-hover"><small>{hover.name_en}</small><strong>{hover.name_th}</strong><span>{format(hover[metric.id],metric.decimals)} <small>{metric.unit}</small></span></div>}
  <div className="map-legend"><strong>{metric.label}</strong><div className="gradient"/><div className="legend-values"><span>0</span><span>{format(max,metric.decimals)} {metric.unit}</span></div><small>สีเข้ม = ค่ามาก · คลิกเขตเพื่อดูรายละเอียด</small></div>
  <div className="north">N<span>↑</span></div>
 </div>;
}
