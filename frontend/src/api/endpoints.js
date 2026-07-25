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
export const preLogin = (data) => client.post("/auth/pre-login", data);
export const loginWithOTP = (data) => client.post("/auth/login-with-otp", data);
export const me = () => client.get("/auth/me");
export const registerUser = (payload) => client.post("/auth/register", payload);
export const changePassword = (data) => client.post("/auth/change-password", data);
export const forgotPassword = (data) => client.post("/auth/forgot-password", data);
export const resetPasswordWithOTP = (data) => client.post("/auth/reset-password", data);
export const listUsers = () => client.get("/users");
export const toggleUserActive = (id) => client.patch(`/users/${id}/toggle-active`);
export const resetUserOTP = (id) => client.post(`/users/${id}/reset-otp`);
export const resetPasswordSelfService = (payload) => client.post("/auth/reset-password-self-service", payload);

// -- Dashboard -----------------------------------------------------------
export const getHospitalStats = () => client.get("/dashboard/stats");
export const getAnalytics = () => client.get("/analytics");

// -- Patients --------------------------------------------------------------
export const listPatients = (district) => client.get("/patients", { params: { district } });
export const getMyPatientRecord = () => client.get("/patients/me");
export const getPatient = (id) => client.get(`/patients/${id}`);
export const createPatient = (payload) => client.post("/patients", payload);
export const updatePatient = (id, payload) => client.patch(`/patients/${id}`, payload);
export const deletePatient = (id) => client.delete(`/patients/${id}`);

// -- Doctors --------------------------------------------------------------
export const listDoctors = (availableOnly) => client.get("/doctors", { params: { available_only: availableOnly } });
export const createDoctor = (payload) => client.post("/doctors", payload);
export const updateDoctor = (id, payload) => client.patch(`/doctors/${id}`, payload);

// -- Appointments --------------------------------------------------------------
export const listAppointments = (params) => client.get("/appointments", { params });
export const createAppointment = (payload) => client.post("/appointments", payload);
export const updateAppointment = (id, payload) => client.patch(`/appointments/${id}`, payload);
export const cancelAppointment = (id) => client.delete(`/appointments/${id}`);

// -- Lab --------------------------------------------------------------
export const listLabResults = (patientId) => client.get("/lab", { params: { patient_id: patientId } });
export const createLabResult = (payload) => client.post("/lab", payload);

// -- Pharmacy --------------------------------------------------------------
export const listPharmacyItems = (lowStockOnly) => client.get("/pharmacy", { params: { low_stock_only: lowStockOnly } });
export const createPharmacyItem = (payload) => client.post("/pharmacy", payload);
export const updatePharmacyItem = (id, payload) => client.patch(`/pharmacy/${id}`, payload);

// -- Medical Records --------------------------------------------------------------
export const listMedicalRecords = (patientId) => client.get("/medical-records", { params: { patient_id: patientId } });
export const createMedicalRecord = (payload) => client.post("/medical-records", payload);

// -- Alerts --------------------------------------------------------------
export const listAlerts = (status) => client.get("/alerts", { params: { status } });
export const updateAlert = (id, status) => client.patch(`/alerts/${id}`, { status });

// -- ML: Dengue outbreak prediction --------------------------------------------------------------
export const trainDengueModel = () => client.post("/ml/train/dengue");
export const predictDistrict = (district) => client.get(`/ml/predict/district/${encodeURIComponent(district)}`);
export const getRiskMap = () => client.get("/ml/risk-map");

// -- ML: Patient diagnosis prediction --------------------------------------------------------------
export const trainDiagnosisModel = () => client.post("/ml/train/diagnosis");
export const predictPatientDiagnosis = (payload) => client.post("/ml/predict/patient", payload);