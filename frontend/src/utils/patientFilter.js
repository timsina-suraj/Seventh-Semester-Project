// Client-side patient search used by pickers/dropdowns — matches on name or
// patient number (both plaintext fields; phone/address stay encrypted and
// aren't searchable this way, mirroring the backend's own search scope).
export function filterPatientsBySearch(patients, term) {
  const query = term.trim().toLowerCase();
  if (!query) return patients;
  return patients.filter(
    (p) => p.full_name.toLowerCase().includes(query) || p.patient_number.toLowerCase().includes(query)
  );
}
