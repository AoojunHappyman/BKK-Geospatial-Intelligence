import type {District,Metric,MetricKey} from './types';
import {format} from './types';
import {useApi} from './api';
import {CompareButton,Link,useFlow} from './ExploreFlow';

export const zones=['กรุงเทพกลาง','กรุงเทพใต้','กรุงเทพเหนือ','กรุงเทพตะวันออก','กรุงธนเหนือ','กรุงธนใต้'];
export function useZone(){const {params,update}=useFlow();const zone=zones.includes(params.get('zone')||'')?params.get('zone')!:'';return {zone,setZone:(value:string)=>update({zone:value,district:null})};}
export function ZoneSelect(){const {zone,setZone}=useZone();return <label className="metric-select">กลุ่มเขต<select aria-label="กลุ่มเขต" value={zone} onChange={e=>setZone(e.target.value)}><option value="">ทั้งหมด 50 เขต</option>{zones.map(z=><option key={z}>{z}</option>)}</select></label>;}

export function DistrictTable({rows,metric}:{rows:District[];metric:Metric}){
 const {params,update,selected}=useFlow();
 const fields=['name_th','population_total','area_km2','metric','compare'] as const;
 type SortKey=typeof fields[number];
 const sort=fields.includes(params.get('sort') as SortKey)?params.get('sort') as SortKey:'metric';
 const direction=params.get('dir')==='asc'?'asc':'desc';
 const value=(r:District,key:SortKey):number|string|null=>key==='metric'?r[metric.id]:key==='compare'?Number(selected.includes(r.district_code)):r[key];
 const sorted=[...rows].sort((a,b)=>{
  const av=value(a,sort),bv=value(b,sort);
  if(av==null||bv==null)return av==null?(bv==null?0:1):-1;
  const result=typeof av==='string'?av.localeCompare(String(bv),'th'):Number(av)-Number(bv);
  return (direction==='asc'?result:-result)||a.district_code.localeCompare(b.district_code);
 });
 const labels=['เขต / District','ประชากร','พื้นที่ (ตร.กม.)',metric.label,'เปรียบเทียบ'];
 function change(key:SortKey){update({sort:key,dir:sort===key?(direction==='asc'?'desc':'asc'):key==='name_th'?'asc':'desc'});}
 return <><div className="table-actions"><span>{sorted.length} เขตตามตัวกรอง · คลิกหัวตารางเพื่อจัดเรียง</span><a className="button" aria-label="ส่งออก CSV ตามตัวกรอง" href={'/api/export/districts.csv?districts='+encodeURIComponent(sorted.map(r=>r.district_code).join(','))}>ส่งออก CSV ({sorted.length} เขต)</a></div><div className="table-wrap"><table><thead><tr>{fields.map((key,i)=><th key={key} aria-sort={sort===key?(direction==='asc'?'ascending':'descending'):'none'}><button className="sort-heading" onClick={()=>change(key)}>{labels[i]} {sort===key?(direction==='asc'?'↑':'↓'):'↕'}</button>{key==='metric'&&<small>{metric.unit}</small>}</th>)}</tr></thead><tbody>{sorted.map(r=><tr key={r.district_code} data-district={r.district_code}><td><Link to={'/district/'+r.district_code}>{r.name_th}<small>{r.name_en} · {r.district_code}</small><small>{r.zone}</small></Link></td><td>{format(r.population_total)}</td><td>{format(r.area_km2,2)}</td><td className="metric-value">{format(r[metric.id],metric.decimals)}</td><td><CompareButton id={r.district_code}/></td></tr>)}</tbody></table>{!rows.length&&<div className="empty">ไม่พบเขตที่ตรงกับคำค้น</div>}</div></>;
}

export type Benchmarks=Record<MetricKey,{value:number|null;method:string}>;
export function BenchmarkBadge({value,benchmark,unit,decimals=1}:{value:number|null;benchmark?:Benchmarks[MetricKey];unit:string;decimals?:number}){
 if(!benchmark||benchmark.value==null||value==null)return <small className="benchmark-badge">ไม่มีข้อมูลเปรียบเทียบ</small>;
 const delta=value-benchmark.value;
 return <div className="benchmark-badge"><strong>{Math.abs(delta)<1e-9?'เท่ากับ':delta>0?'สูงกว่า':'ต่ำกว่า'}ค่าอ้างอิง กทม.</strong><span>เฉลี่ย {format(benchmark.value,decimals)} {unit}</span><small>{benchmark.method}</small></div>;
}

type Pyramid={reference_period:string;classified_total:number;excluded_total:number;bands:{age_start:number;label:string;male:number;female:number}[]};
export function PopulationPyramid({code}:{code:string}){
 const {data,loading,error}=useApi<Pyramid>('/api/districts/'+code+'/population-pyramid');
 if(loading)return <section className="panel" role="status">กำลังโหลดโครงสร้างอายุแยกเพศ…</section>;
 if(error)return <section className="panel" role="alert">{error}</section>;
 if(!data)return null;
 const max=Math.max(...data.bands.flatMap(b=>[b.male,b.female]),1);
 return <section className="panel pyramid-panel" aria-label="พีระมิดประชากร"><div className="eyebrow">AGE × SEX / {data.reference_period}</div><h2>พีระมิดประชากร</h2><p className="muted">ประชากรไทยที่แจกแจงอายุ {format(data.classified_total)} คน · ช่วงละ 5 ปี</p><div className="pyramid-legend"><span>ชาย ←</span><span>อายุ (ปี)</span><span>→ หญิง</span></div><div className="pyramid-axis"><span>{format(max)} คน</span><span>0</span><span>{format(max)} คน</span></div><div className="pyramid-chart" role="img" aria-label="ชายด้านซ้าย หญิงด้านขวา ใช้มาตราส่วนจำนวนคนเดียวกันทั้งสองฝั่ง">{data.bands.map(b=><div className="pyramid-row" key={b.age_start} title={`${b.label} ปี: ชาย ${format(b.male)} หญิง ${format(b.female)} คน`}><div className="pyramid-side male"><i style={{width:`${100*b.male/max}%`}}/><span>{format(b.male)}</span></div><b>{b.label}</b><div className="pyramid-side female"><i style={{width:`${100*b.female/max}%`}}/><span>{format(b.female)}</span></div></div>)}</div><p className="fineprint">ชาย/หญิงตามการรายงานของต้นทาง · 100+ รวมอายุ 100 และ 101+ · ไม่รวมอีก {format(data.excluded_total)} คนในหมวดนอกชุดแจกแจงอายุ</p><details><summary>ดูตารางอายุแยกเพศ</summary><table><thead><tr><th>อายุ</th><th>ชาย</th><th>หญิง</th></tr></thead><tbody>{data.bands.map(b=><tr key={b.age_start}><td>{b.label}</td><td>{b.male}</td><td>{b.female}</td></tr>)}</tbody></table></details></section>;
}
