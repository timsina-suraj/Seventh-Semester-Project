import { useEffect, useState } from "react";
import * as api from "../../api/endpoints";

export default function Profile() {
  const [patient, setPatient] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .getMyPatientRecord()
      .then((res) => setPatient(res.data))
      .catch((err) =>
        setError(err.response?.data?.detail || "No patient record is linked to your account yet — ask reception to link it.")
      );
  }, []);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>My Profile</h1>
        </div>
      </div>

      {error && <div className="empty-state">{error}</div>}

      {patient && (
        <div className="card" style={{ maxWidth: 480 }}>
          <div className="form-group">
            <label>Patient number</label>
            <div>{patient.patient_number}</div>
          </div>
          <div className="form-group">
            <label>Name</label>
            <div>{patient.full_name}</div>
          </div>
          <div className="form-group">
            <label>Date of birth</label>
            <div>{patient.date_of_birth}</div>
          </div>
          <div className="form-group">
            <label>Gender</label>
            <div>{patient.gender}</div>
          </div>
          <div className="form-group">
            <label>Blood group</label>
            <div>{patient.blood_group}</div>
          </div>
          <div className="form-group">
            <label>District</label>
            <div>{patient.district}</div>
          </div>
          <div className="form-group">
            <label>Province / Municipality</label>
            <div>{[patient.province, patient.municipality].filter(Boolean).join(" / ") || "—"}</div>
          </div>
          <div className="form-group">
            <label>Phone</label>
            <div>{patient.phone || "—"}</div>
          </div>
          <div className="form-group">
            <label>Emergency contact</label>
            <div>{patient.emergency_contact || "—"}</div>
          </div>
          <div className="form-group">
            <label>Allergies</label>
            <div>{patient.allergies || "—"}</div>
          </div>
        </div>
      )}
    </div>
  );
}
