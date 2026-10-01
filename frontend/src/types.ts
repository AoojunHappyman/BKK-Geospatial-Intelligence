import type { FeatureCollection, Geometry } from 'geojson';
export type MetricKey='population_density'|'population_total'|'older_share'|'transit_coverage'|'transit_station_count'|'healthcare_per_100k'|'healthcare_facility_count'|'risk_location_count';
export type District={district_code:string;name_th:string;name_en:string;reference_period:string;area_km2:number;male_population:number;female_population:number;age_0_14:number;age_15_59:number;age_60_plus:number;age_classified_total:number;outside_age_series:number;updated_at:string}&Record<MetricKey,number|null>;
export type Metric={id:MetricKey;label:string;label_en:string;unit:string;dimension:string;sources:string[];period:string;decimals:number;description:string};
export type Dataset={source_id:string;name:string;organization:string;url:string;retrieved_at:string;last_updated:string|null;reference_period:string;license:string|null;raw_format:string;notes:string;row_count:number};
export type GeoData=FeatureCollection<Geometry>;
export const format=(value:number|null|undefined,decimals=0)=>value==null?'ไม่มีข้อมูล':new Intl.NumberFormat('th-TH',{maximumFractionDigits:decimals}).format(value);

