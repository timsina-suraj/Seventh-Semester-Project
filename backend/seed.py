"""
MediShield — Bulk Demo Data Seeder
====================================
Populates every table with realistic Nepali demographic data so the app is
fully demonstrable immediately after running.

Runs against a plain sync engine (settings.sync_database_url) — seeding is
a one-off script, not part of request handling, so it doesn't need the
app's async runtime. Assumes the schema already exists (`alembic upgrade
head` — this script does not create tables).

Seeded accounts get a real password and is_active=True directly, bypassing
the first-login OTP flow, purely for demo/grading convenience. The actual
OTP-first-login flow is fully implemented and covered by the integration
tests (tests/integration/test_auth_flow.py) — create a new staff/patient
account through the app to see it end-to-end.

Usage (from backend/):
    python seed.py

Re-running is safe — each section is skipped if data already exists.
Clear the DB first to get a fresh seed:
    del MediShield_db.db   (Windows)
    rm MediShield_db.db    (Linux/Mac)
"""
import json
import random
import secrets
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 — registers all ORM classes
from app.config import settings
from app.models.admin import Admin
from app.models.alert import Alert
from app.models.appointment import Appointment
from app.models.audit_log import AuditLog
from app.models.doctor import Doctor
from app.models.doctor_availability import DoctorAvailability
from app.models.document import VALID_DOCUMENT_CATEGORIES, Document
from app.models.inventory import Inventory
from app.models.lab_result import LabResult
from app.models.lab_technician import LabTechnician
from app.models.lab_test import LabTest
from app.models.login_log import LoginLog
from app.models.medical_history import MedicalHistory
from app.models.medical_record import MedicalRecord
from app.models.medicine import Medicine
from app.models.medicine_administration import MedicineAdministration
from app.models.nurse import Nurse
from app.models.patient import Patient
from app.models.patient_conditions import PatientCondition
from app.models.patient_vitals import PatientVitals
from app.models.prescription import Prescription, PrescriptionItem
from app.models.receptionist import Receptionist
from app.models.user import User
from app.security.auth import hash_password

engine = create_engine(settings.sync_database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# ── Helpers ───────────────────────────────────────────────────────────────────

def ago(days=0, hours=0):
    return datetime.now(timezone.utc) - timedelta(days=days, hours=hours)

def future(days=0, hours=0):
    return datetime.now(timezone.utc) + timedelta(days=days, hours=hours)

def dob_for_age(age: int) -> date:
    return date.today().replace(year=date.today().year - age)

def next_weekday_at(days_from_today: int, hour: int) -> datetime:
    """A datetime `days_from_today` days out, snapped to the nearest
    Mon-Fri, at `hour`:00 — keeps seeded appointments inside the 10am-4pm
    Mon-Fri availability windows seeded for every doctor below."""
    d = date.today() + timedelta(days=days_from_today)
    while d.weekday() > 4:  # Sat=5, Sun=6
        d += timedelta(days=1)
    return datetime(d.year, d.month, d.day, hour, 0, tzinfo=timezone.utc)

rng = random.Random(42)  # fixed seed → reproducible data

# ── 1. Admin ───────────────────────────────────────────────────────────────────
print("\n── Admin ─────────────────────────────────────")

if not db.query(User).filter(User.email == "admin@example.com").first():
    admin_user = User(
        email="admin@example.com",
        role="admin",
        password_hash=hash_password("Admin@12345"),
        is_active=True,
        must_change_password=False,
    )
    db.add(admin_user)
    db.flush()
    db.add(Admin(user_id=admin_user.id, name="System Administrator"))
    print("  + admin@example.com")
else:
    admin_user = db.query(User).filter(User.email == "admin@example.com").first()
    print("  ~ admin already exists, skipping")

db.flush()

# ── 2. Doctors ─────────────────────────────────────────────────────────────────
print("\n── Doctors ──────────────────────────────────")

DOCTOR_DATA = [
    ("Dr. Anjali Sharma", "General Medicine", "General Physician"),
    ("Dr. Bikash Thapa", "Infectious Disease", "Infectious Disease Specialist"),
    ("Dr. Sushil Adhikari", "Internal Medicine", "Internal Medicine"),
    ("Dr. Meena Koirala", "Pediatrics", "Pediatrician"),
    ("Dr. Ramesh Poudel", "Emergency Medicine", "Emergency Physician"),
    ("Dr. Sunita Rai", "General Medicine", "General Physician"),
    ("Dr. Dipak Joshi", "Tropical Medicine", "Tropical Medicine Specialist"),
    ("Dr. Priya Karmacharya", "Infectious Disease", "Dengue Specialist"),
]

doctors = []
if db.query(Doctor).count() == 0:
    for i, (full_name, department, specialization) in enumerate(DOCTOR_DATA):
        email = f"{full_name.split()[1].lower()}@example.com"
        user = User(email=email, role="doctor", password_hash=hash_password("Doctor@1234"), is_active=True, must_change_password=False)
        db.add(user)
        db.flush()
        doc = Doctor(
            user_id=user.id,
            employee_id=f"DOC-{i + 1:04d}",
            full_name=full_name,
            department=department,
            specialization=specialization,
            license_number=f"NMC-{10000 + i}",
        )
        db.add(doc)
        db.flush()
        # Mon-Fri, 10am-4pm availability for every seeded doctor.
        for day in range(0, 5):
            db.add(DoctorAvailability(doctor_id=doc.id, day_of_week=day, start_time=time(10, 0), end_time=time(16, 0)))
        doctors.append(doc)
        print(f"  + {doc.full_name} ({doc.department}) — {email}")
else:
    doctors = db.query(Doctor).all()
    print(f"  ~ {len(doctors)} doctors already exist, skipping")

db.flush()

# ── 3. Nurses, Receptionists, Lab Technicians ───────────────────────────────────
print("\n── Nurses / Receptionists / Lab Technicians ──")

nurses = []
if db.query(Nurse).count() == 0:
    NURSE_DATA = [("Nirmala Gurung", "General Ward", "Morning"), ("Kabita Lama", "Emergency", "Evening")]
    for i, (full_name, department, shift) in enumerate(NURSE_DATA):
        email = f"nurse{i + 1}@example.com"
        user = User(email=email, role="nurse", password_hash=hash_password("Nurse@1234"), is_active=True, must_change_password=False)
        db.add(user)
        db.flush()
        n = Nurse(user_id=user.id, employee_id=f"NUR-{i + 1:04d}", full_name=full_name, department=department, shift=shift)
        db.add(n)
        db.flush()
        nurses.append(n)
        print(f"  + {full_name} ({department}, {shift}) — {email}")
else:
    nurses = db.query(Nurse).all()
    print(f"  ~ {len(nurses)} nurses already exist, skipping")

if db.query(Receptionist).count() == 0:
    RECEPTIONIST_DATA = ["Sarita Bhandari", "Manoj Shrestha"]
    for i, full_name in enumerate(RECEPTIONIST_DATA):
        email = f"recept{i + 1}@example.com"
        user = User(email=email, role="receptionist", password_hash=hash_password("Recept@1234"), is_active=True, must_change_password=False)
        db.add(user)
        db.flush()
        db.add(Receptionist(user_id=user.id, employee_id=f"REC-{i + 1:04d}", full_name=full_name))
        print(f"  + {full_name} — {email}")
else:
    print(f"  ~ {db.query(Receptionist).count()} receptionists already exist, skipping")

if db.query(LabTechnician).count() == 0:
    LAB_TECH_DATA = [("Rajesh Magar", "Hematology"), ("Sabina Rana", "Serology")]
    for i, (full_name, department) in enumerate(LAB_TECH_DATA):
        email = f"labtech{i + 1}@example.com"
        user = User(email=email, role="lab_technician", password_hash=hash_password("LabTech@1234"), is_active=True, must_change_password=False)
        db.add(user)
        db.flush()
        db.add(LabTechnician(user_id=user.id, employee_id=f"LAB-{i + 1:04d}", full_name=full_name, department=department))
        print(f"  + {full_name} ({department}) — {email}")
else:
    print(f"  ~ {db.query(LabTechnician).count()} lab technicians already exist, skipping")

db.flush()

# ── 4. Patients (with linked login accounts) ───────────────────────────────────
print("\n── Patients ─────────────────────────────────")

PATIENT_DATA = [
    # name, province, municipality, phone, age, gender, blood_group, district
    ("Sita Gurung", "Bagmati", "Baneshwor", "9800100001", 29, "Female", "O+", "Kathmandu"),
    ("Ram Bahadur Magar", "Bagmati", "Sauraha", "9800100002", 41, "Male", "B+", "Chitawan"),
    ("Sunita Tamang", "Bagmati", "Patan", "9800100003", 35, "Female", "A+", "Lalitpur"),
    ("Hari Prasad Khanal", "Bagmati", "Hetauda-5", "9800100004", 58, "Male", "AB+", "Makwanpur"),
    ("Bimala Thapa", "Gandaki", "Pokhara-8", "9800100005", 23, "Female", "O-", "Kaski"),
    ("Suresh KC", "Koshi", "Biratnagar-3", "9800100006", 32, "Male", "B-", "Morang"),
    ("Manisha Shrestha", "Koshi", "Dharan-12", "9800100007", 27, "Female", "A-", "Sunsari"),
    ("Dipendra Rai", "Koshi", "Birtamod", "9800100008", 45, "Male", "O+", "Morang"),
    ("Rekha Devi Shah", "Madhesh", "Birgunj-4", "9800100009", 38, "Female", "AB-", "Parsa"),
    ("Nabin Adhikari", "Lumbini", "Butwal-11", "9800100010", 22, "Male", "B+", "Rupandehi"),
    ("Kamala Bhattarai", "Madhesh", "Janakpur-2", "9800100011", 50, "Female", "O+", "Dhanusa"),
    ("Lokraj Poudel", "Bagmati", "Bharatpur-8", "9800100012", 33, "Male", "A+", "Chitawan"),
    ("Asmita Pandey", "Lumbini", "Nepalgunj-5", "9800100013", 19, "Female", "B+", "Banke"),
    ("Gopal Chaudhary", "Sudurpashchim", "Dhangadhi-3", "9800100014", 62, "Male", "O+", "Kailali"),
    ("Puja Maharjan", "Bagmati", "Kirtipur", "9800100015", 31, "Female", "A+", "Kathmandu"),
    ("Binod Tamang", "Bagmati", "Bhaktapur-7", "9800100016", 44, "Male", "AB+", "Bhaktapur"),
    ("Sarita Neupane", "Lumbini", "Tulsipur-2", "9800100017", 26, "Female", "B-", "Dang"),
    ("Rajan Basnet", "Gandaki", "Pokhara-12", "9800100018", 37, "Male", "O-", "Kaski"),
    ("Laxmi Karki", "Bagmati", "Hetauda-2", "9800100019", 29, "Female", "A+", "Makwanpur"),
    ("Arjun Shrestha", "Bagmati", "Lalitpur-4", "9800100020", 53, "Male", "B+", "Lalitpur"),
]

patients = []
if db.query(Patient).count() == 0:
    year = date.today().year
    for i, (name, province, municipality, phone, age, gender, blood_group, district) in enumerate(PATIENT_DATA):
        uemail = f"patient{i + 1:02d}@example.com"
        pu = db.query(User).filter(User.email == uemail).first()
        if not pu:
            pu = User(email=uemail, role="patient", password_hash=hash_password("Patient@1234"), is_active=True, must_change_password=False)
            db.add(pu)
            db.flush()

        p = Patient(
            user_id=pu.id,
            patient_number=f"PAT-{year}-{i + 1:04d}",
            full_name=name,
            date_of_birth=dob_for_age(age),
            gender=gender,
            blood_group=blood_group,
            encrypted_phone=phone,
            encrypted_address=json.dumps({"province": province, "municipality": municipality}),
            district=district,
            encrypted_emergency_contact=phone,
            allergies=rng.choice([None, None, None, "Penicillin", "Dust", "Peanuts"]),
        )
        db.add(p)
        db.flush()
        patients.append(p)
        print(f"  + [{district:12s}] {name} (age {age}, {gender}) — {p.patient_number}")
else:
    patients = db.query(Patient).all()
    print(f"  ~ {len(patients)} patients already exist, skipping")

db.flush()

# ── 5. Medical History / Patient Conditions ─────────────────────────────────────
print("\n── Medical History / Patient Conditions ──────")

PAST_CONDITIONS = ["Typhoid Fever", "Malaria", "Chickenpox", "Pneumonia", "Appendectomy"]
CHRONIC_CONDITIONS = ["Diabetes", "Hypertension", "Obesity", "Asthma"]

if db.query(MedicalHistory).count() == 0:
    history_rows, condition_rows = [], []
    for patient in patients:
        if rng.random() < 0.4:
            history_rows.append(MedicalHistory(
                patient_id=patient.id,
                condition_name=rng.choice(PAST_CONDITIONS),
                diagnosed_date=ago(days=rng.randint(200, 2000)).date(),
                notes="Fully recovered, no ongoing treatment.",
            ))
        if rng.random() < 0.3:
            condition_rows.append(PatientCondition(
                patient_id=patient.id,
                condition=rng.choice(CHRONIC_CONDITIONS),
                status=rng.choice(["Active", "Managed"]),
                diagnosed_date=ago(days=rng.randint(100, 1500)).date(),
            ))
    db.add_all(history_rows + condition_rows)
    db.flush()
    print(f"  + {len(history_rows)} medical history rows, {len(condition_rows)} condition rows created")
else:
    print(f"  ~ medical history already exists, skipping")

# ── 6. Appointments ────────────────────────────────────────────────────────────
print("\n── Appointments ─────────────────────────────")

APPT_REASONS = [
    "High fever and body aches", "Routine dengue screening", "Platelet count check",
    "Follow-up after dengue treatment", "Headache and rash", "Severe joint pain",
    "Persistent vomiting", "General check-up", "Blood test review", "Dengue fever monitoring",
]
APPT_STATUS_PAST = ["Completed", "Completed", "Completed", "Cancelled", "No-show"]
APPT_STATUS_FUTURE = ["Pending", "Confirmed"]

appointments = []
if db.query(Appointment).count() == 0:
    for patient in patients:
        for _ in range(rng.randint(1, 3)):
            days_offset = rng.randint(-30, 14)
            hour = rng.choice([10, 11, 13, 14, 15])
            when = next_weekday_at(days_offset, hour)
            status = rng.choice(APPT_STATUS_FUTURE) if days_offset > 0 else rng.choice(APPT_STATUS_PAST)
            appt = Appointment(
                patient_id=patient.id,
                doctor_id=rng.choice(doctors).id,
                appointment_date=when,
                reason=rng.choice(APPT_REASONS),
                status=status,
            )
            db.add(appt)
            appointments.append(appt)
    db.flush()
    print(f"  + {len(appointments)} appointments created")
else:
    appointments = db.query(Appointment).all()
    print(f"  ~ {len(appointments)} appointments already exist, skipping")

# ── 7. Medical Records ─────────────────────────────────────────────────────────
print("\n── Medical Records ──────────────────────────")

SYMPTOM_SETS = [
    "High fever (39C+), severe headache, body aches",
    "Fever, rash on torso and arms, retro-orbital pain",
    "Persistent vomiting, severe joint pain, fatigue",
    "Sudden high fever, platelet drop, dengue test positive",
    "Mild fever, headache, general malaise",
    "Fever 3 days, myalgia, loss of appetite",
    "Asymptomatic - routine screening",
]
DIAGNOSES_POS = [
    "Dengue Fever - Classic (NS1+)", "Dengue Haemorrhagic Fever - Stage II",
    "Dengue Fever with Warning Signs - platelet < 80k", "Dengue Fever - IgM positive, day 5",
    "Severe Dengue - requires ICU monitoring",
]
DIAGNOSES_NEG = [
    "Viral fever - non-dengue", "Typhoid fever (confirmed by Widal)",
    "Malaria (RDT negative for dengue)", "Common cold / influenza", "No pathology - routine visit",
]
TREATMENT_PLANS_POS = [
    "Supportive care, oral rehydration, monitor platelet count daily.",
    "Admit for IV fluids and close monitoring of warning signs.",
    "Bed rest, paracetamol for fever, repeat CBC in 48 hours.",
]
TREATMENT_PLANS_NEG = [
    "Symptomatic treatment, rest and fluids, review if symptoms persist.",
    "Routine follow-up in 1 week if no improvement.",
]

completed_appointments = [a for a in appointments if a.status == "Completed"]

medical_records = []
if db.query(MedicalRecord).count() == 0:
    mr_rows = []
    for patient in patients:
        for _ in range(rng.randint(1, 3)):
            is_dengue = rng.random() < 0.55
            linked_appt = next((a for a in completed_appointments if a.patient_id == patient.id), None)
            mr = MedicalRecord(
                patient_id=patient.id,
                doctor_id=linked_appt.doctor_id if linked_appt else rng.choice(doctors).id,
                appointment_id=linked_appt.id if linked_appt else None,
                encrypted_symptoms=rng.choice(SYMPTOM_SETS),
                encrypted_diagnosis=rng.choice(DIAGNOSES_POS if is_dengue else DIAGNOSES_NEG),
                encrypted_notes="Advised rest and fluid intake. Follow up in 3 days.",
                encrypted_treatment_plan=rng.choice(TREATMENT_PLANS_POS if is_dengue else TREATMENT_PLANS_NEG),
                follow_up_date=(ago(days=-rng.randint(3, 10))).date() if is_dengue else None,
                ml_dengue_predicted=is_dengue,
                ml_dengue_probability=round(rng.uniform(0.72, 0.97) if is_dengue else rng.uniform(0.03, 0.28), 3),
                created_at=ago(days=rng.randint(1, 60)),
            )
            db.add(mr)
            mr_rows.append(mr)
    db.flush()
    medical_records = mr_rows
    print(f"  + {len(mr_rows)} medical records created")
else:
    medical_records = db.query(MedicalRecord).all()
    print(f"  ~ {len(medical_records)} medical records already exist, skipping")

# ── 8. Prescriptions ────────────────────────────────────────────────────────────
print("\n── Prescriptions ─────────────────────────────")

DENGUE_PRESCRIPTION_ITEMS = [
    dict(medicine_name="Paracetamol 500mg", dosage="500mg", frequency="3 times a day", duration="5 days", instructions="After meals"),
    dict(medicine_name="ORS Sachets", dosage="1 sachet", frequency="As needed", duration="Until recovery", instructions="Dissolve in 1L water"),
]
OTHER_PRESCRIPTION_ITEMS = [
    dict(medicine_name="Vitamin C 500mg", dosage="500mg", frequency="Once a day", duration="10 days", instructions="With breakfast"),
]

if db.query(Prescription).count() == 0:
    count = 0
    for mr in medical_records:
        if not mr.ml_dengue_predicted and rng.random() > 0.3:
            continue
        items = DENGUE_PRESCRIPTION_ITEMS if mr.ml_dengue_predicted else OTHER_PRESCRIPTION_ITEMS
        presc = Prescription(patient_id=mr.patient_id, doctor_id=mr.doctor_id, medical_record_id=mr.id, created_at=mr.created_at)
        db.add(presc)
        db.flush()
        for item in items:
            db.add(PrescriptionItem(prescription_id=presc.id, **item))
        count += 1
    db.flush()
    print(f"  + {count} prescriptions created")
else:
    print(f"  ~ {db.query(Prescription).count()} prescriptions already exist, skipping")

# ── 9. Lab Tests / Results ───────────────────────────────────────────────────────
print("\n── Lab Tests / Results ───────────────────────")

TEST_NAMES = ["CBC", "Dengue NS1", "Dengue IgM/IgG", "Platelet Count", "Hematocrit"]

if db.query(LabTest).count() == 0:
    test_count, result_count = 0, 0
    for patient in patients:
        for _ in range(rng.randint(1, 3)):
            test = LabTest(
                patient_id=patient.id,
                doctor_id=rng.choice(doctors).id,
                test_name=rng.choice(TEST_NAMES),
                status="Requested",
                requested_at=ago(days=rng.randint(0, 20)),
            )
            db.add(test)
            db.flush()
            test_count += 1
            if rng.random() < 0.7:  # most requested tests already have a result
                test.status = "Completed"
                db.add(LabResult(
                    lab_test_id=test.id,
                    result_value=f"{rng.randint(45000, 250000)} /uL" if "Platelet" in test.test_name else rng.choice(["Positive", "Negative"]),
                    completed_at=test.requested_at + timedelta(hours=rng.randint(2, 48)),
                ))
                result_count += 1
    db.flush()
    print(f"  + {test_count} lab tests, {result_count} results created")
else:
    print(f"  ~ {db.query(LabTest).count()} lab tests already exist, skipping")

# ── 10. Patient Vitals / Medicine Administration ────────────────────────────────
print("\n── Vitals / Medication Administration ────────")

if db.query(PatientVitals).count() == 0 and nurses:
    vitals_rows, admin_rows = [], []
    for patient in patients:
        for _ in range(rng.randint(0, 2)):
            vitals_rows.append(PatientVitals(
                patient_id=patient.id,
                nurse_id=rng.choice(nurses).id,
                temperature=round(rng.uniform(36.5, 40.0), 1),
                blood_pressure=f"{rng.randint(100, 140)}/{rng.randint(65, 90)}",
                heart_rate=rng.randint(60, 110),
                oxygen_level=round(rng.uniform(94.0, 99.5), 1),
                weight=round(rng.uniform(45.0, 90.0), 1),
                recorded_at=ago(days=rng.randint(0, 15), hours=rng.randint(0, 12)),
            ))
        if rng.random() < 0.3:
            admin_rows.append(MedicineAdministration(
                patient_id=patient.id,
                nurse_id=rng.choice(nurses).id,
                medicine="Paracetamol 500mg",
                dose="1 tablet",
                time_given=ago(days=rng.randint(0, 10), hours=rng.randint(0, 12)),
            ))
    db.add_all(vitals_rows + admin_rows)
    db.flush()
    print(f"  + {len(vitals_rows)} vitals rows, {len(admin_rows)} medication administration rows created")
else:
    print(f"  ~ vitals already exist, skipping")

# ── 11. Pharmacy Inventory (Medicines + Inventory) ───────────────────────────────
print("\n── Pharmacy ─────────────────────────────────")

MEDICINES = [
    ("Paracetamol 500mg", "Analgesic", "tablets", 500, 100),
    ("IV Fluids - Normal Saline", "IV Fluid", "bottles", 15, 20),
    ("Platelet Concentrate", "Blood Product", "units", 8, 10),
    ("ORS Sachets", "Rehydration", "sachets", 300, 50),
    ("Dextrose 5% IV", "IV Fluid", "bottles", 40, 15),
    ("Chloroquine 250mg", "Antimalarial", "tablets", 120, 30),
    ("Aspirin 75mg", "Analgesic", "tablets", 6, 25),
    ("Ibuprofen 400mg", "Analgesic", "tablets", 200, 40),
    ("Metoclopramide Injection", "Antiemetic", "ampoules", 50, 20),
    ("Ondansetron 4mg", "Antiemetic", "tablets", 90, 30),
    ("Vitamin C 500mg", "Supplement", "tablets", 180, 50),
    ("Zinc Sulphate 20mg", "Supplement", "tablets", 100, 25),
    ("Dengue Rapid Test Kit", "Diagnostic", "kits", 45, 20),
    ("NS1 Antigen Test Kit", "Diagnostic", "kits", 12, 15),
    ("Disposable Syringes 5ml", "Consumable", "pcs", 400, 100),
    ("Examination Gloves (L)", "Consumable", "pairs", 200, 80),
    ("Surgical Masks", "Consumable", "pcs", 350, 100),
    ("Hand Sanitizer 500ml", "Consumable", "bottles", 22, 10),
    ("Bandages (Crepe 6in)", "Consumable", "rolls", 60, 20),
    ("Thermometer Digital", "Equipment", "units", 15, 5),
]

if db.query(Medicine).count() == 0:
    for name, category, unit, qty, threshold in MEDICINES:
        medicine = Medicine(name=name, category=category, unit=unit)
        db.add(medicine)
        db.flush()
        db.add(Inventory(medicine_id=medicine.id, quantity=qty, reorder_threshold=threshold))
    db.flush()
    print(f"  + {len(MEDICINES)} medicines + inventory rows created")
else:
    print(f"  ~ {db.query(Medicine).count()} medicines already exist, skipping")

# ── 11b. Documents ──────────────────────────────────────────────────────────────
print("\n── Documents ─────────────────────────────────")

if db.query(Document).count() == 0:
    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    doc_rows = []
    for patient in patients:
        for _ in range(rng.randint(0, 2)):
            category = rng.choice(VALID_DOCUMENT_CATEGORIES)
            content = (
                f"Demo {category} document for {patient.full_name} ({patient.patient_number}).\n"
                f"Generated by seed.py — placeholder content for demo purposes.\n"
            ).encode()
            stored_filename = f"{secrets.token_hex(16)}.txt"
            (upload_root / stored_filename).write_bytes(content)
            doc_rows.append(Document(
                patient_id=patient.id,
                uploaded_by_user_id=admin_user.id,
                category=category,
                original_filename=f"{category.replace(' ', '_').lower()}_{patient.patient_number}.txt",
                stored_filename=stored_filename,
                content_type="text/plain",
                file_size=len(content),
                uploaded_at=ago(days=rng.randint(0, 20)),
            ))
    db.add_all(doc_rows)
    db.flush()
    print(f"  + {len(doc_rows)} documents created")
else:
    print(f"  ~ {db.query(Document).count()} documents already exist, skipping")

# ── 12. Alerts ──────────────────────────────────────────────────────────────────
print("\n── Alerts ───────────────────────────────────")

ALERT_DATA = [
    dict(alert_type="district_risk", district="Chitawan", risk_level="High", status="open",
         message="Dengue case surge detected in Chitawan. 18 new cases in 7 days. Activate response protocol.", date=ago(days=2)),
    dict(alert_type="district_risk", district="Kathmandu", risk_level="Medium", status="open",
         message="Rising dengue positivity rate in Kathmandu (34%). Increased surveillance recommended.", date=ago(days=1)),
    dict(alert_type="district_risk", district="Kaski", risk_level="High", status="acknowledged",
         message="High dengue risk in Kaski - rainfall and temperature conditions favour Aedes breeding.", date=ago(days=5)),
    dict(alert_type="district_risk", district="Parsa", risk_level="Low", status="resolved",
         message="Parsa dengue activity returning to baseline. Continue routine surveillance.", date=ago(days=10)),
    dict(alert_type="district_risk", district="Banke", risk_level="Medium", status="open",
         message="Banke dengue cases up 22% vs last month. Fogging campaign initiated.", date=ago(hours=6)),
    dict(alert_type="patient_diagnosis", district="Lalitpur", risk_level="High", status="open",
         message="Patient flagged dengue-positive by AI screening. Immediate doctor review required.", date=ago(hours=3)),
    dict(alert_type="patient_diagnosis", district="Kathmandu", risk_level="High", status="acknowledged",
         message="Patient platelet count critically low (48k). Admitted for monitoring.", date=ago(days=3)),
    dict(alert_type="district_risk", district="Morang", risk_level="Medium", status="open",
         message="Morang reports cluster of dengue cases near industrial zone. Larval surveys underway.", date=ago(days=4)),
    dict(alert_type="patient_diagnosis", district="Sunsari", risk_level="High", status="resolved",
         message="Patient discharged after dengue fever recovery. Follow-up in 2 weeks.", date=ago(days=7)),
    dict(alert_type="district_risk", district="Dhanusa", risk_level="Low", status="open",
         message="Dhanusa reports early-season dengue activity. Pre-monsoon vector control recommended.", date=ago(hours=12)),
]

if db.query(Alert).count() == 0:
    db.add_all([Alert(**a) for a in ALERT_DATA])
    db.flush()
    print(f"  + {len(ALERT_DATA)} alerts created")
else:
    print(f"  ~ {db.query(Alert).count()} alerts already exist, skipping")

# ── 13. Security demo data (OTP / login / audit logs) ────────────────────────────
print("\n── Security logs ─────────────────────────────")

if db.query(LoginLog).count() == 0:
    all_users = db.query(User).all()
    log_rows = []
    for u in rng.sample(all_users, min(10, len(all_users))):
        log_rows.append(LoginLog(user_id=u.id, attempted_email=u.email, status="success",
                                  ip_address="127.0.0.1", device="Mozilla/5.0 (demo seed)", login_time=ago(days=rng.randint(0, 10))))
    log_rows.append(LoginLog(user_id=None, attempted_email="unknown@example.com", status="failed",
                              ip_address="203.0.113.5", device="curl/8.0", login_time=ago(hours=2)))
    db.add_all(log_rows)
    db.flush()
    print(f"  + {len(log_rows)} login log entries created")
else:
    print(f"  ~ {db.query(LoginLog).count()} login logs already exist, skipping")

if db.query(AuditLog).count() == 0:
    audit_rows = [
        AuditLog(user_id=admin_user.id, action="created_staff_account", entity_type="user", entity_id=doctors[0].user_id, ip_address="127.0.0.1", timestamp=ago(days=6)),
        AuditLog(user_id=admin_user.id, action="registered_patient", entity_type="patient", entity_id=patients[0].id, ip_address="127.0.0.1", timestamp=ago(days=5)),
        AuditLog(user_id=admin_user.id, action="changed_password", entity_type="user", entity_id=admin_user.id, ip_address="127.0.0.1", timestamp=ago(days=1)),
    ]
    db.add_all(audit_rows)
    db.flush()
    print(f"  + {len(audit_rows)} audit log entries created")
else:
    print(f"  ~ {db.query(AuditLog).count()} audit logs already exist, skipping")

# ── Commit ─────────────────────────────────────────────────────────────────────
db.commit()

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 52)
print("  MediShield — Seed Complete")
print("=" * 52)
print(f"  Users              : {db.query(User).count():>4}")
print(f"  Doctors            : {db.query(Doctor).count():>4}")
print(f"  Nurses             : {db.query(Nurse).count():>4}")
print(f"  Receptionists      : {db.query(Receptionist).count():>4}")
print(f"  Lab Techs          : {db.query(LabTechnician).count():>4}")
print(f"  Patients           : {db.query(Patient).count():>4}")
print(f"  Appointments       : {db.query(Appointment).count():>4}")
print(f"  Medical Records    : {db.query(MedicalRecord).count():>4}")
print(f"  Prescriptions      : {db.query(Prescription).count():>4}")
print(f"  Lab Tests          : {db.query(LabTest).count():>4}")
print(f"  Lab Results        : {db.query(LabResult).count():>4}")
print(f"  Medicines          : {db.query(Medicine).count():>4}")
print(f"  Patient Vitals     : {db.query(PatientVitals).count():>4}")
print(f"  Documents          : {db.query(Document).count():>4}")
print(f"  Alerts             : {db.query(Alert).count():>4}")
print("=" * 52)
print("\n  Default credentials (all is_active=True, no OTP needed)")
print("  ─────────────────────────────────────────────")
print("  admin@example.com     / Admin@12345")
print("  recept1@example.com   / Recept@1234")
print("  nurse1@example.com    / Nurse@1234")
print("  labtech1@example.com  / LabTech@1234")
print("  anjali@example.com    / Doctor@1234  (and other doctors)")
print("  patient01@example.com / Patient@1234  (and patient02..20)")
print("=" * 52 + "\n")

db.close()
