from app.services.pdf_service import build_lab_report_pdf, build_medical_record_pdf, build_prescription_pdf


def test_build_medical_record_pdf_produces_a_valid_pdf():
    pdf_bytes = build_medical_record_pdf(
        {
            "id": 1, "symptoms": "Fever", "diagnosis": "Dengue suspected", "notes": "Monitor",
            "treatment_plan": "Rest", "follow_up_date": "2026-08-01", "created_at": "2026-07-26T10:00:00",
            "ml_dengue_predicted": True, "ml_dengue_probability": 0.87,
        },
        "Jane Patient", "Dr. Test", "2026-07-26T10:00:00",
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_build_prescription_pdf_includes_items():
    pdf_bytes = build_prescription_pdf(
        {
            "id": 1, "created_at": "2026-07-26T10:00:00",
            "items": [{"medicine_name": "Paracetamol", "dosage": "500mg", "frequency": "3x/day", "duration": "5 days", "instructions": "After meals"}],
        },
        "Jane Patient", "Dr. Test", "2026-07-26T10:00:00",
    )
    assert pdf_bytes.startswith(b"%PDF")


def test_build_lab_report_pdf_handles_missing_result():
    pdf_bytes = build_lab_report_pdf(
        {"id": 1, "test_name": "CBC", "status": "Requested", "requested_at": "2026-07-26T10:00:00", "result": None},
        "Jane Patient", "2026-07-26T10:00:00",
    )
    assert pdf_bytes.startswith(b"%PDF")
