import {createContext,useContext,useState,useEffect,useRef} from 'react';
import {Link as RouterLink,NavLink as RouterNavLink,useSearchParams,useLocation} from 'react-router-dom';
import type {LinkProps,NavLinkProps} from 'react-router-dom';
import type {District,Metric,GeoData} from './types';
import {format} from './types';
import {CityMap} from './CityMap';

export const DistrictContext=createContext<District[]>([]);
export function useFlow(){
 const rows=useContext(DistrictContext),[params,setParams]=useSearchParams();
 const selected=[...new Set((params.get('districts')||'').split(','))].filter(id=>rows.some(r=>r.district_code===id)).slice(0,4);
 function update(values:Record<string,string|null>,replace=false){setParams(previous=>{const next=new URLSearchParams(previous);for(const [k,v] of Object.entries(values)){if(v)next.set(k,v);else next.delete(k);}return next;},{replace});}
 function toggle(id:string){if(selected.includes(id))update({districts:selected.filter(x=>x!==id).join(',')});else if(selected.length<4)update({districts:[...selected,id].join(',')});}
 return {rows,params,selected,update,toggle};
}
function useTarget(to:LinkProps['to']){
 const {search}=useLocation();
 if(typeof to!=='string'||!to.startsWith('/'))return to;
 const url=new URL(to,'http://local');const params=new URLSearchParams(search);
 url.searchParams.forEach((v,k)=>params.set(k,v));
 return {pathname:url.pathname,search:params.toString(),hash:url.hash};
}
export function Link(props:LinkProps){return <RouterLink {...props} to={useTarget(props.to)}/>;}
export function NavLink(props:NavLinkProps){return <RouterNavLink {...props} to={useTarget(props.to)}/>;}
export function CompareButton({id}:{id:string}){
 const {selected,toggle}=useFlow();const added=selected.includes(id);
 return <button className={added?'compare-added':'primary'} aria-pressed={added} disabled={!added&&selected.length>=4} onClick={()=>toggle(id)}>{added?'นำออกจากการเปรียบเทียบ':selected.length>=4?'เลือกครบ 4 เขตแล้ว':'เพิ่มเพื่อเปรียบเทียบ'}</button>;
}
export function ShareButton(){
 const [message,setMessage]=useState(''),[fallback,setFallback]=useState('');
 const location=useLocation();
 useEffect(()=>{setMessage('');setFallback('');},[location.pathname,location.search]);
 async function share(){try{await navigator.clipboard.writeText(window.location.href);setMessage('คัดลอกลิงก์แล้ว');setFallback('');}catch{setFallback(window.location.href);setMessage('เลือกลิงก์ด้านล่างเพื่อคัดลอก');}}
 return <div className="share-control"><button onClick={share}>แชร์มุมมองนี้ ↗</button><span role={message?'status':undefined}>{message}</span>{fallback&&<input aria-label="ลิงก์สำหรับแชร์" readOnly value={fallback} onFocus={e=>e.target.select()}/>}</div>;
}
export function ComparisonTray(){
 const {rows,selected,toggle,update}=useFlow();if(!selected.length)return null;
 return <section className="comparison-tray" aria-label="เขตที่เลือกเปรียบเทียบ"><div><strong>เปรียบเทียบ {selected.length}/4 เขต</strong><small>{selected.length<2?'เลือกอีก 1 เขตเพื่อเริ่มเปรียบเทียบ':'เลือกได้สูงสุด 4 เขต'}</small></div><div className="tray-chips">{selected.map(id=><button key={id} aria-label={'นำ'+rows.find(r=>r.district_code===id)?.name_th+'ออกจากชุดเปรียบเทียบ'} onClick={()=>toggle(id)}>{rows.find(r=>r.district_code===id)?.name_th} ×</button>)}</div>{selected.length>=2?<Link className="button primary" to="/compare">ดูการเปรียบเทียบ →</Link>:<button disabled>ดูการเปรียบเทียบ</button>}<button onClick={()=>update({districts:null})}>ล้างทั้งหมด</button></section>;
}
export function ExploreMap({geometry,rows,metric,children}:{geometry:GeoData;rows:District[];metric:Metric;children?:React.ReactNode}){
 const {params,update}=useFlow();const row=rows.find(r=>r.district_code===params.get('district'));
 const panelRef=useRef<HTMLElement>(null);
 useEffect(()=>{if(row&&window.matchMedia('(max-width:680px)').matches)panelRef.current?.scrollIntoView({block:'start'});},[row?.district_code]);
 return <div className={'map-layout explore-layout'+(row?' has-selection':'')}><CityMap geometry={geometry} rows={rows} metric={metric} selected={row?.district_code} focusSelected={false} onSelect={id=>update({district:id})}/>{row?<aside ref={panelRef} className="panel district-preview" aria-label="รายละเอียดเขตที่เลือก" onKeyDown={e=>{if(e.key==='Escape')update({district:null});}}><div className="preview-top"><span className="eyebrow">DISTRICT {row.district_code}</span><button aria-label="ปิดรายละเอียดเขต" onClick={()=>update({district:null})}>×</button></div><h2>{row.name_th}</h2><p className="muted">{row.name_en}</p><div className="preview-value"><small>{metric.label}</small><strong>{format(row[metric.id],metric.decimals)}</strong><span>{metric.unit}</span></div><dl><dt>ประชากรทะเบียน</dt><dd>{format(row.population_total)} คน</dd><dt>ข้อมูลประชากร</dt><dd>{row.reference_period}</dd><dt>พื้นที่</dt><dd>{format(row.area_km2,2)} ตร.กม.</dd></dl><p className="fineprint">{metric.description}</p><CompareButton id={row.district_code}/><Link className="button" to={'/district/'+row.district_code}>ดูโปรไฟล์เต็ม →</Link></aside>:children||<aside className="panel selection-hint"><span className="eyebrow">EXPLORE BANGKOK</span><h2>เริ่มจากเขตที่สนใจ</h2><p>คลิกบนแผนที่เพื่อดูรายละเอียด หรือเลือกเขตด้านล่าง</p><label>เลือกเขต<select aria-label="เลือกเขตบนแผนที่" value="" onChange={e=>update({district:e.target.value})}><option value="">เลือกเขต…</option>{rows.map(r=><option key={r.district_code} value={r.district_code}>{r.name_th}</option>)}</select></label></aside>}</div>;
}
