import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./auth";
import Layout from "./components/Layout";
import DocumentDetail from "./pages/DocumentDetail";
import Documents from "./pages/Documents";
import Export from "./pages/Export";
import Help from "./pages/Help";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Profile from "./pages/Profile";
import Register from "./pages/Register";
import Team from "./pages/Team";
import Upload from "./pages/Upload";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) return <p className="center-note">Yükleniyor…</p>;

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  const accountant = user.role === "accountant";
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/documents/:id" element={<DocumentDetail />} />
        {accountant && <Route path="/export" element={<Export />} />}
        {accountant && <Route path="/team" element={<Team />} />}
        <Route path="/profile" element={<Profile />} />
        <Route path="/help" element={<Help />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
