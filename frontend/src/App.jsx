// import { Navigate, Route, Routes } from "react-router-dom";
// import ProtectedRoute from "./auth/ProtectedRoute.jsx";
// import { useAuth } from "./auth/AuthContext.jsx";
// import DashboardLayout from "./layouts/DashboardLayout.jsx";
// import Login from "./pages/Login.jsx";
// import ChangePassword from "./pages/ChangePassword.jsx";
// import Patients from "./pages/Patients.jsx";
// import Doctors from "./pages/Doctors.jsx";
// import Appointments from "./pages/Appointments.jsx";
// import Pharmacy from "./pages/Pharmacy.jsx";
// import AdminDashboard from "./pages/admin/Dashboard.jsx";
// import Analytics from "./pages/admin/Analytics.jsx";
// import RiskMap from "./pages/admin/RiskMap.jsx";
// import Alerts from "./pages/admin/Alerts.jsx";
// import Users from "./pages/admin/Users.jsx";
// import DiagnosisPrediction from "./pages/doctor/DiagnosisPrediction.jsx";
// import Profile from "./pages/patient/Profile.jsx";
// import MyAppointments from "./pages/patient/MyAppointments.jsx";
// import Reports from "./pages/patient/Reports.jsx";

// function RoleHome() {
//   const { user } = useAuth();
//   switch (user.role) {
//     case "admin":
//       return <AdminDashboard />;
//     case "doctor":
//       return <Patients />;
//     case "receptionist":
//       return <Patients />;
//     case "patient":
//       return <Profile />;
//     default:
//       return null;
//   }
// }

// export default function App() {
//   return (
//     <Routes>
//       <Route path="/login" element={<Login />} />

//       <Route element={<ProtectedRoute />}>
//         <Route path="/change-password" element={<ChangePassword />} />
//         <Route element={<DashboardLayout />}>
//           <Route path="/" element={<RoleHome />} />

//           {/* admin + doctor + receptionist */}
//           <Route element={<ProtectedRoute roles={["admin", "doctor", "receptionist"]} />}>
//             <Route path="/patients" element={<Patients />} />
//             <Route path="/appointments" element={<Appointments />} />
//           </Route>

//           {/* admin + doctor */}
//           <Route element={<ProtectedRoute roles={["admin", "doctor"]} />}>
//             <Route path="/risk-map" element={<RiskMap />} />
//             <Route path="/alerts" element={<Alerts />} />
//           </Route>

//           {/* admin + receptionist */}
//           <Route element={<ProtectedRoute roles={["admin", "receptionist"]} />}>
//             <Route path="/pharmacy" element={<Pharmacy />} />
//           </Route>

//           {/* admin only */}
//           <Route element={<ProtectedRoute roles={["admin"]} />}>
//             <Route path="/analytics" element={<Analytics />} />
//             <Route path="/doctors" element={<Doctors />} />
//             <Route path="/users" element={<Users />} />
//           </Route>

//           {/* doctor only */}
//           <Route element={<ProtectedRoute roles={["doctor"]} />}>
//             <Route path="/diagnosis" element={<DiagnosisPrediction />} />
//           </Route>

//           {/* patient only */}
//           <Route element={<ProtectedRoute roles={["patient"]} />}>
//             <Route path="/my-appointments" element={<MyAppointments />} />
//             <Route path="/my-reports" element={<Reports />} />
//           </Route>
//         </Route>
//       </Route>

//       <Route path="*" element={<Navigate to="/" replace />} />
//     </Routes>
//   );
// }


import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./auth/ProtectedRoute.jsx";
import { useAuth } from "./auth/AuthContext.jsx";
import DashboardLayout from "./layouts/DashboardLayout.jsx";
import Login from "./pages/Login.jsx";
import ChangePassword from "./pages/ChangePassword.jsx";
import Patients from "./pages/Patients.jsx";
import Doctors from "./pages/Doctors.jsx";
import Appointments from "./pages/Appointments.jsx";
import Pharmacy from "./pages/Pharmacy.jsx";
import RegisterPatient from "./pages/patients/RegisterPatient.jsx";
import AddDoctor from "./pages/doctors/AddDoctor.jsx";
import BookAppointment from "./pages/appointments/BookAppointment.jsx";
import AddPharmacyItem from "./pages/pharmacy/AddPharmacyItem.jsx";
import AdminDashboard from "./pages/admin/Dashboard.jsx";
import Analytics from "./pages/admin/Analytics.jsx";
import RiskMap from "./pages/admin/RiskMap.jsx";
import Alerts from "./pages/admin/Alerts.jsx";
import Users from "./pages/admin/Users.jsx";
import ReceptionistDashboard from "./pages/receptionist/Dashboard.jsx";
import DoctorDashboard from "./pages/doctor/Dashboard.jsx";
import DiagnosisPrediction from "./pages/doctor/DiagnosisPrediction.jsx";
import PatientDashboard from "./pages/patient/Dashboard.jsx";
import Profile from "./pages/patient/Profile.jsx";
import MyAppointments from "./pages/patient/MyAppointments.jsx";
import Reports from "./pages/patient/Reports.jsx";
import DengueCheck from "./pages/patient/DengueCheck.jsx";
import Receptionists from "./pages/admin/Receptionists.jsx";
import ForgotPassword from "./pages/ForgotPassword.jsx";

function RoleHome() {
  const { user } = useAuth();
  switch (user.role) {
    case "admin":
      return <AdminDashboard />;
    case "doctor":
      return <DoctorDashboard />;
    case "receptionist":
      return <ReceptionistDashboard />;
    case "patient":
      return <PatientDashboard />;
    default:
      return null;
  }
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/change-password" element={<ChangePassword />} />
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<RoleHome />} />

          {/* admin + doctor + receptionist */}
          <Route element={<ProtectedRoute roles={["admin", "doctor", "receptionist"]} />}>
            <Route path="/patients" element={<Patients />} />
            <Route path="/appointments" element={<Appointments />} />
          </Route>

          {/* admin + doctor */}
          <Route element={<ProtectedRoute roles={["admin", "doctor"]} />}>
            <Route path="/risk-map" element={<RiskMap />} />
            <Route path="/alerts" element={<Alerts />} />
          </Route>

          {/* admin + receptionist — manage forms */}
          <Route element={<ProtectedRoute roles={["admin", "receptionist"]} />}>
            <Route path="/pharmacy" element={<Pharmacy />} />
            <Route path="/pharmacy/add" element={<AddPharmacyItem />} />
            <Route path="/patients/register" element={<RegisterPatient />} />
            <Route path="/appointments/book" element={<BookAppointment />} />
          </Route>

          {/* admin only */}
          <Route element={<ProtectedRoute roles={["admin"]} />}>
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/doctors" element={<Doctors />} />
            <Route path="/doctors/add" element={<AddDoctor />} />
            <Route path="/receptionists" element={<Receptionists />} />
            <Route path="/users" element={<Users />} />
          </Route>

          {/* doctor only */}
          <Route element={<ProtectedRoute roles={["doctor"]} />}>
            <Route path="/diagnosis" element={<DiagnosisPrediction />} />
          </Route>

          {/* patient only */}
          <Route element={<ProtectedRoute roles={["patient"]} />}>
            <Route path="/my-profile" element={<Profile />} />
            <Route path="/my-appointments" element={<MyAppointments />} />
            <Route path="/my-reports" element={<Reports />} />
            <Route path="/dengue-check" element={<DengueCheck />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}