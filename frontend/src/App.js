import React from "react";
import "@/index.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider, useApp } from "@/contexts/AppContext";
import LoginPage from "@/pages/LoginPage";
import DashboardPage from "@/pages/DashboardPage";
import ConsensusPage from "@/pages/ConsensusPage";
import SmartHomePage from "@/pages/SmartHomePage";
import ChatPage from "@/pages/ChatPage";
import BrainPage from "@/pages/BrainPage";

function Protected({ children }) {
  const { user, loading } = useApp();
  if (loading) return <div className="min-h-screen bg-dashboard flex items-center justify-center text-cyan">Loading Hub3…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<Protected><DashboardPage /></Protected>} />
          <Route path="/consensus" element={<Protected><ConsensusPage /></Protected>} />
          <Route path="/smart-home" element={<Protected><SmartHomePage /></Protected>} />
          <Route path="/chat" element={<Protected><ChatPage /></Protected>} />
          <Route path="/brain" element={<Protected><BrainPage /></Protected>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}
