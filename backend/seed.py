"""
MediShield — Bulk Demo Data Seeder
====================================
Populates every table with realistic Nepali demographic data so the app
is fully demonstrable immediately after running.

Usage (from backend/):
    python seed.py

Re-running is safe — each section is skipped if data already exists.
Clear the DB first to get a fresh seed:
    del MediShield_db.db   (Windows)
    rm MediShield_db.db    (Linux/Mac)
"""

import random
from datetime import datetime, timedelta, timezone

import app.models  # noqa: F401 — registers all ORM classes before create_all
from app.database import Base, SessionLocal, engine
from app.models.alert import Alert
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.lab import LabResult
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.pharmacy import PharmacyItem
from app.models.user import User
from app.security.auth import hash_password

# ── Create all tables ─────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ── Helpers ───────────────────────────────────────────────────────────────────

def ago(days=0, hours=0):
    """Return a UTC datetime offset back from now."""
    return datetime.now(timezone.utc) - timedelta(days=days, hours=hours)

def future(days=0, hours=0):
    return datetime.now(timezone.utc) + timedelta(days=days, hours=hours)

rng = random.Random(42)  # fixed seed → reproducible data

# ── 1. Users (admin + staff accounts) ─────────────────────────────────────────
print("\n── Users ────────────────────────────────────")

STAFF_ACCOUNTS = [
    dict(username="admin",        email="admin@example.com",        role="admin",        password="Admin@12345"),
    dict(username="receptionist1",email="recept1@example.com",      role="receptionist", password="Recept@1234"),
    dict(username="receptionist2",email="recept2@example.com",      role="receptionist", password="Recept@1234"),
    dict(username="dr_anjali",    email="anjali@example.com",       role="doctor",       password="Doctor@1234"),
    dict(username="dr_bikash",    email="bikash@example.com",       role="doctor",       password="Doctor@1234"),
    dict(username="dr_sushil",    email="sushil@example.com",       role="doctor",       password="Doctor@1234"),
    dict(username="dr_meena",     email="meena@example.com",        role="doctor",       password="Doctor@1234"),
]

created_users = {}
for acc in STAFF_ACCOUNTS:
    if not db.query(User).filter(User.email == acc["email"]).first():
        u = User(
            email=acc["email"],
            role=acc["role"],
            password_hash=hash_password(acc["password"]),
            must_change_password=True,
        )
        db.add(u)
        db.flush()
        created_users[acc["username"]] = u
    else:
        existing = db.query(User).filter(User.email == acc["email"]).first()
        created_users[acc["username"]] = existing

db.flush()

# ── 2. Doctors ─────────────────────────────────────────────────────────────────
print("\n── Doctors ──────────────────────────────────")

DOCTOR_DATA = [
    {
        "full_name": "Dr. Anjali Sharma",
        "specialization": "General Physician",
        "phone": "9801000001",
        "is_available": True,
    },
    {
        "full_name": "Dr. Bikash Thapa",
        "specialization": "Infectious Disease",
        "phone": "9801000002",
        "is_available": True,
    },
    {
        "full_name": "Dr. Sushil Adhikari",
        "specialization": "Internal Medicine",
        "phone": "9801000003",
        "is_available": True,
    },
    {
        "full_name": "Dr. Meena Koirala",
        "specialization": "Pediatrics",
        "phone": "9801000004",
        "is_available": True,
    },
    {
        "full_name": "Dr. Ramesh Poudel",
        "specialization": "Emergency Medicine",
        "phone": "9801000005",
        "is_available": False,
    },
    {
        "full_name": "Dr. Sunita Rai",
        "specialization": "General Physician",
        "phone": "9801000006",
        "is_available": True,
    },
    {
        "full_name": "Dr. Dipak Joshi",
        "specialization": "Tropical Medicine",
        "phone": "9801000007",
        "is_available": True,
    },
    {
        "full_name": "Dr. Priya Karmacharya",
        "specialization": "Dengue Specialist",
        "phone": "9801000008",
        "is_available": False,
    },
]

doctors = []

if db.query(Doctor).count() == 0:
    for d in DOCTOR_DATA:

        doc = Doctor(
            full_name=d["full_name"],
            specialization=d["specialization"],
            encrypted_phone=d["phone"],
            is_available=d["is_available"],
        )

        db.add(doc)
        db.flush()

        doctors.append(doc)

        print(
            f"  + {doc.full_name} "
            f"({doc.specialization})"
        )

else:
    doctors = db.query(Doctor).all()
    print(
        f"  ~ {len(doctors)} doctors already exist, skipping"
    )
    
db.flush()

# ── 3. Patients (with linked login accounts) ───────────────────────────────────
print("\n── Patients ─────────────────────────────────")

NEPAL_DISTRICTS = [
    "Kathmandu", "Lalitpur", "Bhaktapur", "Chitawan", "Pokhara",
    "Biratnagar", "Dharan", "Butwal", "Nepalgunj", "Hetauda",
    "Birgunj", "Dhangadhi", "Tulsipur", "Janakpur", "Bharatpur",
]

PATIENT_DATA = [
    # name, address, phone, age, gender, district
    ("Sita Gurung",        "Baneshwor, Kathmandu",  "9800100001", 29, "Female", "Kathmandu"),
    ("Ram Bahadur Magar",  "Sauraha, Chitawan",     "9800100002", 41, "Male",   "Chitawan"),
    ("Sunita Tamang",      "Patan, Lalitpur",       "9800100003", 35, "Female", "Lalitpur"),
    ("Hari Prasad Khanal", "Hetauda-5",             "9800100004", 58, "Male",   "Hetauda"),
    ("Bimala Thapa",       "Pokhara-8",             "9800100005", 23, "Female", "Pokhara"),
    ("Suresh KC",          "Biratnagar-3",          "9800100006", 32, "Male",   "Biratnagar"),
    ("Manisha Shrestha",   "Dharan-12",             "9800100007", 27, "Female", "Dharan"),
    ("Dipendra Rai",       "Birtamod, Jhapa",       "9800100008", 45, "Male",   "Biratnagar"),
    ("Rekha Devi Shah",    "Birgunj-4",             "9800100009", 38, "Female", "Birgunj"),
    ("Nabin Adhikari",     "Butwal-11",             "9800100010", 22, "Male",   "Butwal"),
    ("Kamala Bhattarai",   "Janakpur-2",            "9800100011", 50, "Female", "Janakpur"),
    ("Lokraj Poudel",      "Bharatpur-8",           "9800100012", 33, "Male",   "Bharatpur"),
    ("Asmita Pandey",      "Nepalgunj-5",           "9800100013", 19, "Female", "Nepalgunj"),
    ("Gopal Chaudhary",    "Dhangadhi-3",           "9800100014", 62, "Male",   "Dhangadhi"),
    ("Puja Maharjan",      "Kirtipur, Kathmandu",   "9800100015", 31, "Female", "Kathmandu"),
    ("Binod Tamang",       "Bhaktapur-7",           "9800100016", 44, "Male",   "Bhaktapur"),
    ("Sarita Neupane",     "Tulsipur-2",            "9800100017", 26, "Female", "Tulsipur"),
    ("Rajan Basnet",       "Pokhara-12",            "9800100018", 37, "Male",   "Pokhara"),
    ("Laxmi Karki",        "Hetauda-2",             "9800100019", 29, "Female", "Hetauda"),
    ("Arjun Shrestha",     "Lalitpur-4",            "9800100020", 53, "Male",   "Lalitpur"),
]

patients = []
if db.query(Patient).count() == 0:
    for i, (name, address, phone, age, gender, district) in enumerate(PATIENT_DATA):
        # Create a linked patient user account
        uname = f"patient{i+1:02d}"
        uemail = f"{uname}@example.com"
        pu = db.query(User).filter(User.email == uemail).first()
        if not pu:
            pu = User(
                email=uemail,
                role="patient",
                password_hash=hash_password("Patient@1234"),
                must_change_password=False,
            )
            db.add(pu)
            db.flush()

        p = Patient(
            user_id=pu.id,
            encrypted_name=name,
            encrypted_address=address,
            encrypted_phone=phone,
            age=age,
            gender=gender,
            district=district,
        )
        db.add(p)
        db.flush()
        patients.append(p)
        print(f"  + [{district:12s}] {name} (age {age}, {gender})")
else:
    patients = db.query(Patient).all()
    print(f"  ~ {len(patients)} patients already exist, skipping")

db.flush()

# ── 4. Appointments ────────────────────────────────────────────────────────────
print("\n── Appointments ─────────────────────────────")

APPT_REASONS = [
    "High fever and body aches",
    "Routine dengue screening",
    "Platelet count check",
    "Follow-up after dengue treatment",
    "Headache and rash",
    "Severe joint pain",
    "Persistent vomiting",
    "General check-up",
    "Blood test review",
    "Dengue fever monitoring",
]

APPT_STATUSES = ["scheduled", "completed", "completed", "completed", "cancelled"]

if db.query(Appointment).count() == 0:
    appts = []
    for i, patient in enumerate(patients):
        num_appts = rng.randint(1, 3)
        for j in range(num_appts):
            days_offset = rng.randint(-30, 14)
            status = rng.choice(APPT_STATUSES)
            if days_offset > 0:
                status = "scheduled"
            elif days_offset == 0:
                status = rng.choice(["scheduled", "completed"])
            a = Appointment(
                patient_id=patient.id,
                doctor_id=rng.choice(doctors).id,
                scheduled_at=ago(days=-days_offset, hours=rng.randint(0, 8)),
                reason=rng.choice(APPT_REASONS),
                status=status,
            )
            appts.append(a)
    db.add_all(appts)
    db.flush()
    print(f"  + {len(appts)} appointments created")
else:
    print(f"  ~ {db.query(Appointment).count()} appointments already exist, skipping")

# ── 5. Lab Results ─────────────────────────────────────────────────────────────
print("\n── Lab Results ──────────────────────────────")

LAB_SCENARIOS = [
    # (ns1, igg, igm, fever_days, temp, platelets, wbc, joint_pain, headache, retro, myalgia, rash, result)
    (True,  False, True,  5, 38.9, 85000,  4200, "Moderate", True,  True,  True,  True,  "Positive"),
    (True,  True,  False, 7, 39.5, 62000,  3100, "Severe",   True,  True,  True,  False, "Positive"),
    (False, False, False, 2, 37.2, 210000, 7800, "None",     False, False, False, False, "Negative"),
    (False, True,  False, 4, 37.8, 145000, 6200, "None",     True,  False, False, False, "Negative"),
    (True,  False, False, 3, 38.2, 120000, 5000, "Moderate", True,  False, True,  False, "Positive"),
    (False, False, True,  6, 39.1, 72000,  3800, "Severe",   True,  True,  True,  True,  "Positive"),
    (False, False, False, 1, 36.8, 195000, 8100, "None",     False, False, False, False, "Negative"),
    (True,  True,  True,  8, 40.1, 48000,  2900, "Severe",   True,  True,  True,  True,  "Positive"),
]

if db.query(LabResult).count() == 0:
    lab_rows = []
    for i, patient in enumerate(patients):
        num_labs = rng.randint(1, 3)
        for j in range(num_labs):
            s = rng.choice(LAB_SCENARIOS)
            lr = LabResult(
                patient_id=patient.id,
                ns1_positive=s[0], igg_positive=s[1], igm_positive=s[2],
                fever_duration_days=s[3] + rng.randint(-1, 1),
                body_temperature_c=round(s[4] + rng.uniform(-0.3, 0.3), 1),
                platelet_count=s[5] + rng.randint(-5000, 5000),
                wbc_count=s[6] + rng.randint(-200, 200),
                joint_pain=s[7],
                headache=s[8], retro_orbital_pain=s[9], myalgia=s[10], rash=s[11],
                dengue_test_result=s[12],
                recorded_at=ago(days=rng.randint(1, 45)),
            )
            lab_rows.append(lr)
    db.add_all(lab_rows)
    db.flush()
    print(f"  + {len(lab_rows)} lab results created")
else:
    print(f"  ~ {db.query(LabResult).count()} lab results already exist, skipping")

# ── 6. Medical Records ─────────────────────────────────────────────────────────
print("\n── Medical Records ──────────────────────────")

SYMPTOM_SETS = [
    "High fever (39°C+), severe headache, body aches",
    "Fever, rash on torso and arms, retro-orbital pain",
    "Persistent vomiting, severe joint pain, fatigue",
    "Sudden high fever, platelet drop, dengue test positive",
    "Mild fever, headache, general malaise",
    "Fever 3 days, myalgia, loss of appetite",
    "Asymptomatic — routine screening",
]
DIAGNOSES_POS = [
    "Dengue Fever — Classic (NS1+)",
    "Dengue Haemorrhagic Fever — Stage II",
    "Dengue Fever with Warning Signs — platelet < 80k",
    "Dengue Fever — IgM positive, day 5",
    "Severe Dengue — requires ICU monitoring",
]
DIAGNOSES_NEG = [
    "Viral fever — non-dengue",
    "Typhoid fever (confirmed by Widal)",
    "Malaria (RDT negative for dengue)",
    "Common cold / influenza",
    "No pathology — routine visit",
]

if db.query(MedicalRecord).count() == 0:
    mr_rows = []
    for patient in patients:
        num_records = rng.randint(1, 3)
        for _ in range(num_records):
            is_dengue = rng.random() < 0.55   # 55% dengue-positive
            mr = MedicalRecord(
                patient_id=patient.id,
                doctor_id=rng.choice(doctors).id,
                encrypted_symptoms=rng.choice(SYMPTOM_SETS),
                encrypted_diagnosis=rng.choice(DIAGNOSES_POS if is_dengue else DIAGNOSES_NEG),
                encrypted_lab_result="NS1+, IgM+" if is_dengue else "NS1-, IgM-, IgG-",
                encrypted_prescription="Paracetamol 500mg, 1 tablet 3 times a day" if is_dengue else "Vitamin C 500mg",
                encrypted_prescribed_tests="Dengue Rapid Test, CBC" if is_dengue else "None",
                encrypted_medical_history="No previous major illnesses.",
                encrypted_clinical_history="Patient appeared fatigued and febrile.",
                encrypted_doctor_note="Advised rest and fluid intake. Follow up in 3 days.",
                ml_dengue_predicted=is_dengue,
                ml_dengue_probability=round(rng.uniform(0.72, 0.97) if is_dengue else rng.uniform(0.03, 0.28), 3),
                date=ago(days=rng.randint(1, 60)),
            )
            mr_rows.append(mr)
    db.add_all(mr_rows)
    db.flush()
    print(f"  + {len(mr_rows)} medical records created")
else:
    print(f"  ~ {db.query(MedicalRecord).count()} medical records already exist, skipping")

# ── 7. Pharmacy Inventory ──────────────────────────────────────────────────────
print("\n── Pharmacy ─────────────────────────────────")

PHARMACY_ITEMS = [
    ("Paracetamol 500mg",           "tablets",  500,  100),
    ("IV Fluids — Normal Saline",   "bottles",  15,   20),   # low stock → triggers alert
    ("Platelet Concentrate",        "units",    8,    10),   # low stock
    ("ORS Sachets",                 "sachets",  300,  50),
    ("Dextrose 5% IV",              "bottles",  40,   15),
    ("Chloroquine 250mg",           "tablets",  120,  30),
    ("Aspirin 75mg",                "tablets",  6,    25),   # low stock
    ("Ibuprofen 400mg",             "tablets",  200,  40),
    ("Metoclopramide Injection",    "ampoules", 50,   20),
    ("Ondansetron 4mg",             "tablets",  90,   30),
    ("Vitamin C 500mg",             "tablets",  180,  50),
    ("Zinc Sulphate 20mg",          "tablets",  100,  25),
    ("Dengue Rapid Test Kit",       "kits",     45,   20),
    ("NS1 Antigen Test Kit",        "kits",     12,   15),   # low stock
    ("Disposable Syringes 5ml",     "pcs",      400,  100),
    ("Examination Gloves (L)",      "pairs",    200,  80),
    ("Surgical Masks",              "pcs",      350,  100),
    ("Hand Sanitizer 500ml",        "bottles",  22,   10),
    ("Bandages (Crepe 6\")",        "rolls",    60,   20),
    ("Thermometer Digital",         "units",    15,   5),
]

if db.query(PharmacyItem).count() == 0:
    items = [PharmacyItem(name=n, unit=u, stock_quantity=sq, reorder_threshold=rt)
             for n, u, sq, rt in PHARMACY_ITEMS]
    db.add_all(items)
    db.flush()
    print(f"  + {len(items)} pharmacy items created")
else:
    print(f"  ~ {db.query(PharmacyItem).count()} items already exist, skipping")

# ── 8. Alerts ──────────────────────────────────────────────────────────────────
print("\n── Alerts ───────────────────────────────────")

ALERT_DATA = [
    dict(alert_type="district_risk",    district="Chitawan",   risk_level="High",   status="open",
         message="Dengue case surge detected in Chitawan. 18 new cases in 7 days. Activate response protocol.",
         date=ago(days=2)),
    dict(alert_type="district_risk",    district="Kathmandu",  risk_level="Medium", status="open",
         message="Rising dengue positivity rate in Kathmandu (34%). Increased surveillance recommended.",
         date=ago(days=1)),
    dict(alert_type="district_risk",    district="Pokhara",    risk_level="High",   status="acknowledged",
         message="High dengue risk in Pokhara — rainfall and temperature conditions favour Aedes breeding.",
         date=ago(days=5)),
    dict(alert_type="district_risk",    district="Birgunj",    risk_level="Low",    status="resolved",
         message="Birgunj dengue activity returning to baseline. Continue routine surveillance.",
         date=ago(days=10)),
    dict(alert_type="district_risk",    district="Nepalgunj",  risk_level="Medium", status="open",
         message="Nepalgunj dengue cases up 22% vs last month. Fogging campaign initiated.",
         date=ago(hours=6)),
    dict(alert_type="patient_diagnosis",district="Lalitpur",   risk_level="High",   status="open",
         message="Patient #3 (Sunita Tamang) flagged dengue-positive by AI screening. Immediate doctor review required.",
         date=ago(hours=3)),
    dict(alert_type="patient_diagnosis",district="Kathmandu",  risk_level="High",   status="acknowledged",
         message="Patient #1 (Sita Gurung) platelet count critically low (48k). Admitted for monitoring.",
         date=ago(days=3)),
    dict(alert_type="district_risk",    district="Biratnagar", risk_level="Medium", status="open",
         message="Biratnagar reports cluster of dengue cases near industrial zone. Larval surveys underway.",
         date=ago(days=4)),
    dict(alert_type="patient_diagnosis",district="Dharan",     risk_level="High",   status="resolved",
         message="Patient #7 (Manisha Shrestha) discharged after dengue fever recovery. Follow-up in 2 weeks.",
         date=ago(days=7)),
    dict(alert_type="district_risk",    district="Janakpur",   risk_level="Low",    status="open",
         message="Janakpur reports early-season dengue activity. Pre-monsoon vector control recommended.",
         date=ago(hours=12)),
]

if db.query(Alert).count() == 0:
    alert_objs = [Alert(**a) for a in ALERT_DATA]
    db.add_all(alert_objs)
    db.flush()
    print(f"  + {len(alert_objs)} alerts created")
else:
    print(f"  ~ {db.query(Alert).count()} alerts already exist, skipping")

# ── Commit ─────────────────────────────────────────────────────────────────────
db.commit()

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "="*52)
print("  MediShield — Seed Complete")
print("="*52)
print(f"  Users          : {db.query(User).count():>4}")
print(f"  Doctors        : {db.query(Doctor).count():>4}")
print(f"  Patients       : {db.query(Patient).count():>4}")
print(f"  Appointments   : {db.query(Appointment).count():>4}")
print(f"  Lab Results    : {db.query(LabResult).count():>4}")
print(f"  Medical Records: {db.query(MedicalRecord).count():>4}")
print(f"  Pharmacy Items : {db.query(PharmacyItem).count():>4}")
print(f"  Alerts         : {db.query(Alert).count():>4}")
print("="*52)
print("\n  Default credentials")
print("  ─────────────────────────────────────────────")
print("  admin         / Admin@12345")
print("  receptionist1 / Recept@1234")
print("  dr_anjali     / Doctor@1234")
print("  patient01     / Patient@1234  (and patient02..20)")
print("="*52 + "\n")

db.close()
