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
            <label>Name</label>
            <div>{patient.name}</div>
          </div>
          <div className="form-group">
            <label>Age</label>
            <div>{patient.age}</div>
          </div>
          <div className="form-group">
            <label>Gender</label>
            <div>{patient.gender}</div>
          </div>
          <div className="form-group">
            <label>District</label>
            <div>{patient.district}</div>
          </div>
          <div className="form-group">
            <label>Phone</label>
            <div>{patient.phone || "—"}</div>
          </div>
          <div className="form-group">
            <label>Address</label>
            <div>{patient.address || "—"}</div>
          </div>
        </div>
      )}
    </div>
  );
}
