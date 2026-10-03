import {useEffect,useRef,useState} from 'react';
import type {District,Dataset} from './types';
import {format} from './types';
import {useFlow,Link} from './ExploreFlow';

type Point = District & {population_density:number;transit_coverage:number};
const hasValues=(r:District):r is Point=>r.population_density!==null&&Number.isFinite(r.population_density)&&r.transit_coverage!==null&&Number.isFinite(r.transit_coverage);

export function DensityTransitChart({rows,visibleCodes,datasets}:{rows:District[];visibleCodes:string[];datasets:Dataset[]}){
 const {params,update}=useFlow();
 const [hovered,setHovered]=useState<string|null>(null);
 const scrollRef=useRef<HTMLDivElement>(null);
 const selection=params.get('district'),scope=visibleCodes.join(',');
 useEffect(()=>setHovered(null),[selection,scope]);
 useEffect(()=>{
  const container=scrollRef.current,dot=container?.querySelector('.scatter-point.selected .scatter-dot');
  if(!container||!dot)return;
  const point=dot.getBoundingClientRect(),viewport=container.getBoundingClientRect();
  if(point.left<viewport.left+16||point.right>viewport.right-16)container.scrollLeft+=point.x+point.width/2-viewport.x-viewport.width/2;
 },[selection,scope]);
 const all=rows.filter(hasValues),points=all.filter(r=>visibleCodes.includes(r.district_code));
 const selected=points.find(r=>r.district_code===params.get('district'));
 const detail=points.find(r=>r.district_code===hovered)||selected;
 const meanDensity=all.reduce((s,r)=>s+r.population_density,0)/(all.length||1);
 const meanCoverage=all.reduce((s,r)=>s+r.transit_coverage,0)/(all.length||1);
 const candidate=(r:Point)=>r.population_density>meanDensity&&r.transit_coverage<meanCoverage;
 const candidates=points.filter(candidate).sort((a,b)=>b.population_density-a.population_density||a.district_code.localeCompare(b.district_code));
 const maxDensity=Math.max(5000,Math.ceil(Math.max(0,...all.map(r=>r.population_density))/5000)*5000);
 const x=(v:number)=>80+v*6.6,y=(v:number)=>360-v/maxDensity*300;
 const choose=(id:string)=>update({district:id||null});
 const showMap=()=>document.querySelector('.explore-layout')?.scrollIntoView({block:'start',behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
 return <section className="panel density-transit" aria-labelledby="density-transit-title">
  <div className="eyebrow">POPULATION × RAIL PROXIMITY</div>
  <h2 id="density-transit-title">ความหนาแน่นประชากร × พื้นที่ใกล้รถไฟฟ้า</h2>
  <p className="muted">แต่ละจุดคือหนึ่งเขต · คลิกจุดเพื่อเลือกเขตเดียวกันบนแผนที่ · แสดง {points.length} เขตตามตัวกรอง</p>
  <div className="scatter-layout">
   <div className="scatter-main">
    <div ref={scrollRef} className="scatter-scroll" role="region" aria-label="กราฟกระจายรายเขต" tabIndex={0}>
     {points.length?<svg viewBox="0 0 780 425" role="group" aria-label="ความหนาแน่นประชากรเทียบกับสัดส่วนพื้นที่ใกล้รถไฟฟ้า">
      <text x="80" y="24" className="scatter-axis-title">ความหนาแน่นประชากร (คน / ตร.กม.) ↑</text>
      <rect x="80" y="60" width={x(meanCoverage)-80} height={y(meanDensity)-60} className="scatter-quadrant"/>
      {[0,1,2,3,4].map(i=><g key={i}><line x1="80" x2="740" y1={y(maxDensity*i/4)} y2={y(maxDensity*i/4)} className="scatter-grid"/><text x="70" y={y(maxDensity*i/4)+4} textAnchor="end">{format(maxDensity*i/4)}</text></g>)}
      {[0,20,40,60,80,100].map(v=><g key={v}><line x1={x(v)} x2={x(v)} y1="60" y2="360" className="scatter-grid"/><text x={x(v)} y="382" textAnchor="middle">{v}%</text></g>)}
      <line x1={x(meanCoverage)} x2={x(meanCoverage)} y1="60" y2="360" className="scatter-mean"/>
      <line x1="80" x2="740" y1={y(meanDensity)} y2={y(meanDensity)} className="scatter-mean"/>
      <text x="410" y="415" textAnchor="middle" className="scatter-axis-title">สัดส่วนพื้นที่ใกล้สถานีรถไฟฟ้า 800 ม. (%) →</text>
      {[...points].sort((a,b)=>Number(a.district_code===selected?.district_code)-Number(b.district_code===selected?.district_code)).map(r=><g key={r.district_code} className={'scatter-point'+(candidate(r)?' candidate':'')+(selected?.district_code===r.district_code?' selected':'')} role="button" tabIndex={0} aria-pressed={selected?.district_code===r.district_code} aria-label={`${r.name_th}: ${format(r.population_density)} คน/ตร.กม., พื้นที่ใกล้รถไฟฟ้า ${format(r.transit_coverage,1)}%`} data-district={r.district_code} onClick={()=>choose(r.district_code)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(r.district_code);}if(e.key==='Escape')setHovered(null);}} onMouseEnter={()=>setHovered(r.district_code)} onMouseLeave={()=>setHovered(null)} onFocus={()=>setHovered(r.district_code)} onBlur={()=>setHovered(null)}>
       <title>{r.name_th} · {format(r.population_density)} คน/ตร.กม. · {format(r.transit_coverage,1)}%</title>
       <circle cx={x(r.transit_coverage)} cy={y(r.population_density)} r="12" className="scatter-hit"/>
       <circle cx={x(r.transit_coverage)} cy={y(r.population_density)} r="6" className="scatter-dot"/>
      </g>)}
     </svg>:<p className="empty">ไม่มีเขตที่มีข้อมูลครบทั้งสองตัวชี้วัดในกลุ่มนี้</p>}
    </div>
    <div className="scatter-legend"><span><i/> เขตทั่วไป</span><span><i className="candidate"/> หนาแน่นสูง / พื้นที่ใกล้รถไฟฟ้าน้อยกว่าเฉลี่ย</span><span><i className="selected"/> เขตที่เลือก</span></div>
    <p className="fineprint">เส้นประ = ค่าเฉลี่ยรายเขต ไม่ถ่วงน้ำหนัก จาก {all.length} เขตที่มีข้อมูลครบ: {format(meanDensity)} คน/ตร.กม. และ {format(meanCoverage,1)}% · เกณฑ์คงเดิมเมื่อเปลี่ยนกลุ่มเขต · ไม่รวมข้อมูลที่ขาด {visibleCodes.length-points.length} เขต</p>
   </div>
   <aside className="scatter-detail" aria-label="รายละเอียดจุดบนกราฟ">
    <label>เลือกเขตบนกราฟ<select aria-label="เลือกเขตบนกราฟ" value={selected?.district_code||''} onChange={e=>choose(e.target.value)}><option value="">เลือกเขต…</option>{[...points].sort((a,b)=>a.name_th.localeCompare(b.name_th,'th')).map(r=><option key={r.district_code} value={r.district_code}>{r.name_th}</option>)}</select></label>
    {detail?<><h3>{detail.name_th}</h3><dl><dt>ความหนาแน่นประชากร</dt><dd>{format(detail.population_density)} คน/ตร.กม.</dd><dt>พื้นที่ใกล้รถไฟฟ้า 800 ม.</dt><dd>{format(detail.transit_coverage,1)}%</dd></dl><p>{candidate(detail)?'อยู่ในกลุ่มหนาแน่นสูง แต่สัดส่วนพื้นที่ใกล้รถไฟฟ้าต่ำกว่าค่าเฉลี่ยรายเขต':'ใช้ค่าทั้งสองร่วมกับบริบทพื้นที่เพื่อศึกษาเขตนี้ต่อ'}</p></>:<p>ชี้จุดหรือใช้แป้น Tab เพื่ออ่านค่า กด Enter เพื่อเลือกเขต จุดที่ซ้อนกันเลือกได้จากรายการด้านบน</p>}
    <div className="scatter-selection" role="status">{selected?`เลือก${selected.name_th}บนแผนที่แล้ว`:'ยังไม่ได้เลือกเขต'}</div>
    {selected&&<><button className="primary" onClick={showMap}>ดูเขตที่เลือกบนแผนที่ ↑</button><Link className="button" to={'/district/'+selected.district_code}>ศึกษา{selected.name_th}ต่อ →</Link></>}
   </aside>
  </div>
  <div className="scatter-candidates"><h3>กลุ่มที่อาจเริ่มศึกษาต่อ · {candidates.length} เขต</h3><p className="muted">ความหนาแน่นสูงกว่าเฉลี่ย และพื้นที่ใกล้รถไฟฟ้าต่ำกว่าเฉลี่ย · เรียงตามความหนาแน่น</p><div>{candidates.map(r=><button key={r.district_code} aria-pressed={selected?.district_code===r.district_code} onClick={()=>choose(r.district_code)}>{r.name_th}</button>)}</div>{!candidates.length&&<p>ไม่พบเขตตามเกณฑ์นี้ในกลุ่มที่เลือก</p>}</div>
  <p className="fineprint">เกณฑ์นี้ใช้สำรวจประเด็น ไม่ใช่อันดับความเร่งด่วนลงทุน ประชากรเป็นประชากรทะเบียน ส่วนพื้นที่ใกล้รถไฟฟ้าเป็นรัศมีเส้นตรง 800 เมตร รวมสถานีนอกเขต ไม่ใช่ระยะเดินหรือสัดส่วนประชากรที่เข้าถึงสถานี</p>
  <p className="fineprint">{datasets.filter(d=>['population','transit','osm_transit','districts'].includes(d.source_id)).map(d=>`${d.name} · ${d.reference_period}`).join(' / ')} · ข้อมูลต่างช่วงเวลา <Link to="/data">ดูแหล่งข้อมูลและวิธีคำนวณ ↗</Link></p>
 </section>;
}
