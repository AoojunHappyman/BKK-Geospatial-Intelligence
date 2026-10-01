import {useLocation} from 'react-router-dom';

export function Skeleton(){
 const {pathname}=useLocation();
 const stats=pathname==='/'||pathname.startsWith('/district/');
 const compare=pathname==='/compare';
 return <section className="loading-layout" aria-busy="true" aria-label="กำลังโหลดข้อมูลกรุงเทพมหานคร">
  <span role="status" className="sr-only">กำลังโหลดข้อมูลกรุงเทพมหานคร…</span>
  <div className="skeleton-heading" aria-hidden="true"><div className="skeleton skeleton-line short"/><div className="skeleton skeleton-title"/><div className="skeleton skeleton-line"/></div>
  {stats&&<div className="stats skeleton-stats" aria-hidden="true">{[0,1,2,3].map(n=><div className="stat" key={n}><div className="skeleton skeleton-line"/><div className="skeleton skeleton-number"/><div className="skeleton skeleton-line short"/></div>)}</div>}
  <div className="skeleton skeleton-toolbar" aria-hidden="true"/>
  {compare?<div className="comparison-grid" aria-hidden="true">{[0,1,2,3].map(n=><div key={n} className="skeleton skeleton-chart"/>)}</div>:<><div className="map-layout" aria-hidden="true"><div className="skeleton skeleton-map"/><div className="skeleton skeleton-map"/></div><div className="skeleton skeleton-note" aria-hidden="true"/>{pathname==='/districts'&&<div className="skeleton-table" aria-hidden="true">{[0,1,2,3].map(n=><div className="skeleton skeleton-row" key={n}/>)}</div>}</>}
 </section>;
}
