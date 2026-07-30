# Admin Dashboard — Replace System Status with Activity Charts

## Context

The admin dashboard (`frontend/src/pages/admin/Dashboard.jsx`) has a "System Status" card showing five rows: Database, ML Models, API Server, Pharmacy Alerts, Dengue Alerts. The first three are hardcoded (`ok: true` always) — they display "Operational"/"Loaded"/"Running" regardless of actual system state, so they carry no real information. The last two duplicate stat tiles already shown above the card (`low_stock_items`, `open_alerts`).

This spec replaces that card with two small charts showing real, currently-uncharted hospital activity: an appointments trend and a patient-registrations trend. `recharts` is already a project dependency, used extensively in `frontend/src/pages/admin/Analytics.jsx` for the dengue-model charts — this reuses that same library and visual style, just for operational (not ML) data.

## Data

`GET /dashboard/stats` (`backend/app/routers/dashboard.py`, service logic in `backend/app/services/stats_service.py`, schema in `backend/app/schemas/dashboard.py`) is the endpoint the dashboard already calls once on mount via `api.getHospitalStats()`. It gains two new fields rather than introducing a second endpoint/fetch:

```python
class TrendPoint(BaseModel):
    date: str   # ISO "YYYY-MM-DD"
    count: int

class HospitalStats(BaseModel):
    # ...existing fields unchanged...
    appointments_trend: list[TrendPoint]
    registrations_trend: list[TrendPoint]
```

- `appointments_trend`: one `TrendPoint` per day for the **last 14 days** (today inclusive), `count` = number of `Appointment` rows whose `appointment_date` falls on that day. Appointments are frequent enough day-to-day that a 14-day window is legible.
- `registrations_trend`: one `TrendPoint` per day for the **last 30 days**, `count` = number of `Patient` rows whose `created_at` falls on that day. Registrations are sparser per day, so a longer window is needed to show a visible trend.
- Days with zero activity are included with `count: 0` (zero-filled), not omitted — so the charts render a continuous axis with no gaps, matching how a reader expects a day-by-day trend to look.

Both are computed with one grouped-count query each in `stats_service.py` (`func.date(<column>)` grouped, SQLite-compatible — matches the existing query style already used for the other stats in that file), via a small shared helper that takes the model, the date column, and the window size, and returns the zero-filled list. No new tables, no new endpoint, no new frontend fetch — this rides the existing `getHospitalStats()` call.

## Frontend

In `frontend/src/pages/admin/Dashboard.jsx`:

- Delete the entire "System Status" `<div className="card">` block (currently lines 162–196, everything between the `{/* ── System Status ── */}` comment and the `Hospital Highlights` card that follows it).
- Add two new cards in its place, styled like `Analytics.jsx`'s existing charts (`ResponsiveContainer`, `CartesianGrid`, `Tooltip`, same color/font-size conventions):
  - **"Appointments — Last 14 Days"**: a `LineChart` over `stats.appointments_trend`, `XAxis dataKey="date"`, a single line on `count`.
  - **"New Registrations — Last 30 Days"**: a `BarChart` over `stats.registrations_trend`, `XAxis dataKey="date"`, a single bar series on `count`.
- These two new cards plus the existing "Hospital Highlights" card all live inside the same `grid-2` container (unchanged from today) — `grid-2` already wraps more than two cards two-per-row elsewhere in this codebase (`Analytics.jsx` puts nine cards through the same class), so no new layout primitive is needed. Result: Appointments chart and Registrations chart on the first row, Hospital Highlights on the second row.
- Both new `<XAxis>`es render dense date labels (14–30 ticks) — use `fontSize={11}` and let recharts' default tick spacing thin them out, consistent with how `Analytics.jsx`'s `symptomsData`/`modelRegressionData` axes are sized. No custom tick-skipping logic; if it turns out too dense in practice, that's a follow-up polish item, not blocking.

## Out of scope

- No date-range picker or interactivity beyond hover tooltips (matches every other chart in `Analytics.jsx`).
- No changes to the "Hospital Highlights" card or any other dashboard section.
- No removal of the `low_stock_items`/`open_alerts` stat tiles above the card grid — those stay; only the duplicate rows inside the old System Status card go away.
