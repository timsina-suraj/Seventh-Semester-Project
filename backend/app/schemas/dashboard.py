from pydantic import BaseModel


class HospitalStats(BaseModel):
    total_patients: int
    dengue_cases_flagged: int
    available_doctors: int
    total_appointments: int
    total_lab_results: int
    low_stock_items: int
    open_alerts: int
