import {useEffect,useState} from 'react';
export function useApi<T>(url:string|null){
 const [data,setData]=useState<T|null>(null),[error,setError]=useState(''),[loading,setLoading]=useState(Boolean(url));
 const [loadedUrl,setLoadedUrl]=useState(url);
 useEffect(()=>{setLoadedUrl(url);if(!url){setData(null);setError('');setLoading(false);return;}const controller=new AbortController();setLoading(true);setError('');setData(null);
 fetch(url,{signal:controller.signal}).then(async r=>{if(!r.ok)throw new Error(r.status===404?'ไม่พบข้อมูลที่เลือก':'ไม่สามารถโหลดข้อมูลได้ กรุณาตรวจสอบการเชื่อมต่อแล้วลองใหม่');return r.json() as Promise<T>;})
 .then(setData).catch(e=>{if(e.name!=='AbortError')setError(e.message);}).finally(()=>{if(!controller.signal.aborted)setLoading(false);});
 return()=>controller.abort();},[url]);
 return loadedUrl===url?{data,error,loading}:{data:null,error:'',loading:Boolean(url)};
}
