import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import './i18n';
import Navbar from './components/Navbar';
import TodayPage from './pages/TodayPage';
import MedicationsPage from './pages/MedicationsPage';
import ApprovalsPage from './pages/ApprovalsPage';
import AppointmentsPage from './pages/AppointmentsPage';
import AdherencePage from './pages/AdherencePage';
import ActivityPage from './pages/ActivityPage';
import LoginPage from './pages/LoginPage';
import SOSModal from './components/SOSModal';
import AIModal from './components/AIModal';
import InteractionCheckerModal from './components/InteractionCheckerModal';
import WeeklySummaryModal from './components/WeeklySummaryModal';
import LiveEmailDrawer from './components/LiveEmailDrawer';
import VoiceAssistantModal from './components/VoiceAssistantModal';
import { Mic } from 'lucide-react';
import { useTranslation } from 'react-i18next';

function MainLayout() {
  const { user, loading, triggerRefresh } = useAuth();
  const { i18n } = useTranslation();
  const [currentTab, setCurrentTab] = useState('today');

  // Modal states
  const [isSOSOpen, setIsSOSOpen] = useState(false);
  const [isAIOpen, setIsAIOpen] = useState(false);
  const [isSafetyOpen, setIsSafetyOpen] = useState(false);
  const [isSummaryOpen, setIsSummaryOpen] = useState(false);
  const [isEmailLogOpen, setIsEmailLogOpen] = useState(false);
  const [isVoiceOpen, setIsVoiceOpen] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900 text-white">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="font-bold text-slate-300">Loading AyuCare Hub...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  const renderTab = () => {
    switch (currentTab) {
      case 'today':
        return (
          <TodayPage
            onOpenAI={() => setIsAIOpen(true)}
            onOpenSafety={() => setIsSafetyOpen(true)}
            onOpenSummary={() => setIsSummaryOpen(true)}
            onOpenVoice={() => setIsVoiceOpen(true)}
            onNavigate={(tab) => setCurrentTab(tab)}
          />
        );
      case 'medications':
        return <MedicationsPage onOpenAI={() => setIsAIOpen(true)} />;
      case 'approvals':
        return <ApprovalsPage />;
      case 'appointments':
        return <AppointmentsPage />;
      case 'adherence':
        return <AdherencePage />;
      case 'activity':
        return <ActivityPage />;
      default:
        return <TodayPage />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        onOpenSOS={() => setIsSOSOpen(true)}
        onOpenEmailLog={() => setIsEmailLogOpen(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {renderTab()}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500 font-medium">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AyuCare • Keeping Elders at the Center of Care</span>
          <span className="font-bold text-slate-700">PromptWars x Catalyst • Google Build with AI</span>
          <span>FastAPI • React + Vite • Gemini 2.5 Flash</span>
        </div>
      </footer>

      {/* Modals & Drawers */}
      <SOSModal
        isOpen={isSOSOpen}
        onClose={() => setIsSOSOpen(false)}
        elderName={user.profile_name}
        emergencyPhone="+91 98401 23456"
        onTriggered={() => triggerRefresh()}
      />

      <AIModal
        isOpen={isAIOpen}
        onClose={() => setIsAIOpen(false)}
        isElder={user.role === 'ELDER'}
        onMedsAdded={() => triggerRefresh()}
      />

      <InteractionCheckerModal
        isOpen={isSafetyOpen}
        onClose={() => setIsSafetyOpen(false)}
        currentMedicines={['Metformin 500mg', 'Telmisartan 40mg', 'Atorvastatin 10mg', 'Eco-Aspirin 75mg']}
      />

      <WeeklySummaryModal
        isOpen={isSummaryOpen}
        onClose={() => setIsSummaryOpen(false)}
      />

      <LiveEmailDrawer
        isOpen={isEmailLogOpen}
        onClose={() => setIsEmailLogOpen(false)}
      />

      {/* Floating Multilingual Voice Assistant Button (Hindi / Tamil / English) */}
      <button
        onClick={() => setIsVoiceOpen(true)}
        className="fixed bottom-6 right-6 z-40 bg-gradient-to-tr from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 active:scale-95 text-white p-4 sm:px-5 sm:py-3.5 rounded-full shadow-2xl flex items-center gap-2.5 font-black text-sm tracking-wide ring-4 ring-emerald-200/50 hover:shadow-emerald-500/25 transition group animate-bounce hover:animate-none"
        title="Open Voice Assistant (Hindi / Tamil / English)"
      >
        <Mic className="w-6 h-6" />
        <span className="hidden sm:inline font-bold">
          {i18n.language === 'hi' ? 'आवाज़ सहायक' : i18n.language === 'ta' ? 'குரல் உதவியாளர்' : 'Voice Assistant'}
        </span>
      </button>

      {/* Multilingual Voice Assistant Modal */}
      <VoiceAssistantModal
        isOpen={isVoiceOpen}
        onClose={() => setIsVoiceOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainLayout />
    </AuthProvider>
  );
}
