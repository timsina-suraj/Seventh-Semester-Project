from pydantic import BaseModel


class TrendPoint(BaseModel):
    date: str
    count: int


class HospitalStats(BaseModel):
    total_patients: int
    dengue_cases_flagged: int
    available_doctors: int
    total_appointments: int
    total_lab_results: int
    low_stock_items: int
    open_alerts: int
    appointments_trend: list[TrendPoint]
    registrations_trend: list[TrendPoint]
