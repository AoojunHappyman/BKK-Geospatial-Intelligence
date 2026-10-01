from pydantic import BaseModel
from typing import Any, Literal

class District(BaseModel):
    district_code: str
    name_th: str
    name_en: str
    zone: str
    reference_period: str
    area_km2: float
    population_total: int
    male_population: int
    female_population: int
    population_density: float
    age_0_14: int
    age_15_59: int
    age_60_plus: int
    age_classified_total: int
    outside_age_series: int
    older_share: float | None
    transit_station_count: int | None
    healthcare_facility_count: int | None
    healthcare_per_100k: float | None
    risk_location_count: int | None
    transit_coverage: float | None
    updated_at: Any

class FeatureCollection(BaseModel):
    type: Literal['FeatureCollection'] = 'FeatureCollection'
    features: list[dict[str, Any]]

