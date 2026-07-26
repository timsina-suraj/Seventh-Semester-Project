import client from "./client";

// -- Auth --------------------------------------------------------------
export const login = (email, password) => {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  return client.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
};
export const me = () => client.get("/auth/me");
export const preLogin = (data) => client.post("/auth/pre-login", data);
export const loginWithOTP = (data) => client.post("/auth/login-with-otp", data);
export const setInitialPassword = (data) => client.post("/auth/set-initial-password", data);
export const registerUser = (payload) => client.post("/auth/register", payload);
export const changePassword = (data) => client.post("/auth/change-password", data);
export const forgotPassword = (data) => client.post("/auth/forgot-password", data);
export const resetPasswordWithOTP = (data) => client.post("/auth/reset-password", data);
export const listUsers = () => client.get("/users");
export const toggleUserActive = (id) => client.patch(`/users/${id}/toggle-active`);
export const adminResetPassword = (id) => client.post(`/users/${id}/reset-password`);

// -- Logs (admin) ----------------------------------------------------------
export const listAuditLogs = (params) => client.get("/audit-logs", { params });
export const listLoginLogs = (params) => client.get("/login-logs", { params });

// -- Staff profiles (admin edits to an existing roster row) ---------------------
export const listNurseProfiles = () => client.get("/nurses");
export const updateNurseProfile = (id, payload) => client.patch(`/nurses/${id}`, payload);
export const listReceptionistProfiles = () => client.get("/receptionists");
export const updateReceptionistProfile = (id, payload) => client.patch(`/receptionists/${id}`, payload);
export const listLabTechnicianProfiles = () => client.get("/lab-technicians");
export const updateLabTechnicianProfile = (id, payload) => client.patch(`/lab-technicians/${id}`, payload);

// -- Dashboard -----------------------------------------------------------
export const getHospitalStats = () => client.get("/dashboard/stats");
export const getAnalytics = () => client.get("/analytics");

// -- Patients --------------------------------------------------------------
export const listPatients = (params) => client.get("/patients", { params });
export const getMyPatientRecord = () => client.get("/patients/me");
export const createPatient = (payload) => client.post("/patients", payload);
export const updatePatient = (id, payload) => client.patch(`/patients/${id}`, payload);
export const deletePatient = (id) => client.delete(`/patients/${id}`);

// -- Doctors --------------------------------------------------------------
// Doctor accounts are created via registerUser({ role: "doctor", ... }) so
// the login and the roster row are always created together.
export const listDoctors = (params) => client.get("/doctors", { params });
export const getMyDoctorProfile = () => client.get("/doctors/me");
export const updateDoctor = (id, payload) => client.patch(`/doctors/${id}`, payload);
export const listAvailability = (doctorId) => client.get(`/doctors/${doctorId}/availability`);
export const addAvailability = (doctorId, payload) => client.post(`/doctors/${doctorId}/availability`, payload);
export const removeAvailability = (doctorId, slotId) => client.delete(`/doctors/${doctorId}/availability/${slotId}`);
export const getAvailableSlots = (doctorId, date) =>
  client.get(`/doctors/${doctorId}/available-slots`, { params: { date } });

// -- Appointments --------------------------------------------------------------
export const listAppointments = (params) => client.get("/appointments", { params });
export const createAppointment = (payload) => client.post("/appointments", payload);
export const updateAppointmentStatus = (id, status) => client.patch(`/appointments/${id}`, { status });

// -- Lab --------------------------------------------------------------
export const listLabTests = (params) => client.get("/lab-tests", { params });
export const requestLabTest = (payload) => client.post("/lab-tests", payload);
export const uploadLabResult = (labTestId, payload) => client.post(`/lab-tests/${labTestId}/result`, payload);

// -- Pharmacy --------------------------------------------------------------
export const listPharmacyItems = (lowStockOnly, search) =>
  client.get("/pharmacy", { params: { low_stock_only: lowStockOnly, search } });
export const createPharmacyItem = (payload) => client.post("/pharmacy", payload);
export const updatePharmacyItem = (id, payload) => client.patch(`/pharmacy/${id}`, payload);

// -- Medical Records --------------------------------------------------------------
export const listMedicalRecords = (patientId, extraFilters) =>
  client.get("/medical-records", { params: { patient_id: patientId, ...extraFilters } });
export const createMedicalRecord = (payload) => client.post("/medical-records", payload);

// -- PDF downloads (Module 14) ----------------------------------------------------
const downloadFile = async (url, fallbackName) => {
  const res = await client.get(url, { responseType: "blob" });
  const disposition = res.headers["content-disposition"] || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : fallbackName;
  const contentType = res.headers["content-type"] || "application/octet-stream";
  const blobUrl = window.URL.createObjectURL(new Blob([res.data], { type: contentType }));
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(blobUrl);
};
export const downloadMedicalRecordPdf = (id) => downloadFile(`/medical-records/${id}/pdf`, `medical_record_${id}.pdf`);
export const downloadPrescriptionPdf = (id) => downloadFile(`/prescriptions/${id}/pdf`, `prescription_${id}.pdf`);
export const downloadLabReportPdf = (id) => downloadFile(`/lab-tests/${id}/pdf`, `lab_report_${id}.pdf`);
export const downloadAppointmentReceiptPdf = (id) => downloadFile(`/appointments/${id}/pdf`, `appointment_${id}.pdf`);

// -- Documents (Module 12) ---------------------------------------------------------
export const listDocuments = (patientId, category) =>
  client.get("/documents", { params: { patient_id: patientId, category } });
export const uploadDocument = (patientId, category, file) => {
  const form = new FormData();
  form.append("patient_id", patientId);
  form.append("category", category);
  form.append("file", file);
  return client.post("/documents", form, { headers: { "Content-Type": "multipart/form-data" } });
};
export const downloadDocument = (id, filename) => downloadFile(`/documents/${id}/download`, filename || `document_${id}`);
export const deleteDocument = (id) => client.delete(`/documents/${id}`);

// Returns a temporary object URL + content-type for inline preview (caller
// must window.URL.revokeObjectURL(url) when done, e.g. on modal close).
export const getDocumentPreviewUrl = async (id) => {
  const res = await client.get(`/documents/${id}/download`, { responseType: "blob" });
  const contentType = res.headers["content-type"] || "application/octet-stream";
  return { url: window.URL.createObjectURL(new Blob([res.data], { type: contentType })), contentType };
};

// -- Medical History / Patient Conditions --------------------------------------
export const listMedicalHistory = (patientId) => client.get("/medical-history", { params: { patient_id: patientId } });
export const addMedicalHistory = (payload) => client.post("/medical-history", payload);
export const listPatientConditions = (patientId) => client.get("/patient-conditions", { params: { patient_id: patientId } });
export const addPatientCondition = (payload) => client.post("/patient-conditions", payload);

// -- Prescriptions --------------------------------------------------------------
export const listPrescriptions = (patientId) => client.get("/prescriptions", { params: { patient_id: patientId } });
export const createPrescription = (payload) => client.post("/prescriptions", payload);

// -- Nurse: vitals / medication administration -----------------------------------
export const listPatientVitals = (patientId) => client.get("/patient-vitals", { params: { patient_id: patientId } });
export const recordPatientVitals = (payload) => client.post("/patient-vitals", payload);
export const listMedicineAdministrations = (patientId) => client.get("/medicine-administration", { params: { patient_id: patientId } });
export const recordMedicineAdministration = (payload) => client.post("/medicine-administration", payload);

// -- Alerts --------------------------------------------------------------
export const listAlerts = (status) => client.get("/alerts", { params: { status } });
export const updateAlert = (id, status) => client.patch(`/alerts/${id}`, { status });

// -- ML: Dengue outbreak prediction --------------------------------------------------------------
export const getRiskMap = () => client.get("/ml/risk-map");

// -- ML: Patient diagnosis prediction --------------------------------------------------------------
export const predictPatientDiagnosis = (payload) => client.post("/ml/predict/patient", payload);