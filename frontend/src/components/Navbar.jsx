import React from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import {
  Heart,
  AlertTriangle,
  Globe,
  Type,
  UserCheck,
  ShieldAlert,
  Mail,
  LogOut
} from 'lucide-react';

export default function Navbar({ onOpenSOS, onOpenEmailLog, currentTab, setCurrentTab }) {
  const { t, i18n } = useTranslation();
  const { user, quickSwitchRole, largeFont, toggleLargeFont, changeLanguage, logout } = useAuth();

  const handleLanguageSelect = (langCode) => {
    if (changeLanguage) {
      changeLanguage(langCode);
    } else {
      i18n.changeLanguage(langCode);
      localStorage.setItem('ayucare_lang', langCode);
    }
  };

  const getRoleBadge = (role) => {
    switch (role) {
      case 'ELDER':
        return {
          bg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          label: t('elder_mode')
        };
      case 'CARETAKER':
        return {
          bg: 'bg-blue-100 text-blue-800 border-blue-300',
          label: t('caretaker_mode')
        };
      case 'FAMILY':
        return {
          bg: 'bg-purple-100 text-purple-800 border-purple-300',
          label: t('family_mode')
        };
      default:
        return { bg: 'bg-gray-100 text-gray-800 border-gray-300', label: role };
    }
  };

  const badge = user ? getRoleBadge(user.role) : null;

  return (
    <header className="sticky top-0 z-40 bg-white border-b-2 border-slate-200 shadow-sm">
      {/* Top Banner: Emergency SOS + Role Switcher */}
      <div className="bg-slate-900 text-white px-4 py-2 flex flex-wrap items-center justify-between gap-3 text-sm">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-amber-300 text-xs sm:text-sm uppercase tracking-wider">
            {t('quick_switch')}:
          </span>
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => quickSwitchRole('ELDER')}
              className={`px-2.5 py-1 rounded font-bold text-xs transition ${
                user?.role === 'ELDER'
                  ? 'bg-emerald-500 text-white ring-2 ring-white'
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
              }`}
            >
              👴 Elder (1111)
            </button>
            <button
              onClick={() => quickSwitchRole('CARETAKER')}
              className={`px-2.5 py-1 rounded font-bold text-xs transition ${
                user?.role === 'CARETAKER'
                  ? 'bg-blue-500 text-white ring-2 ring-white'
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
              }`}
            >
              🩺 Caretaker (2222)
            </button>
            <button
              onClick={() => quickSwitchRole('FAMILY')}
              className={`px-2.5 py-1 rounded font-bold text-xs transition ${
                user?.role === 'FAMILY'
                  ? 'bg-purple-500 text-white ring-2 ring-white'
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-200'
              }`}
            >
              👨‍👩‍👧 Family (3333)
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Emergency SOS Button */}
          <button
            onClick={onOpenSOS}
            className="flex items-center gap-2 bg-red-600 hover:bg-red-700 active:scale-95 text-white px-3.5 py-1.5 rounded-full font-black tracking-wide text-xs sm:text-sm shadow-md animate-pulse"
          >
            <ShieldAlert className="w-4 h-4" />
            {t('emergency_sos')}
          </button>

          {/* Email Inspector */}
          <button
            onClick={onOpenEmailLog}
            title="Inspect Background Sent Emails"
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 px-2.5 py-1 rounded border border-slate-700"
          >
            <Mail className="w-3.5 h-3.5 text-amber-400" />
            <span className="hidden sm:inline">Emails</span>
          </button>
        </div>
      </div>

      {/* Main Navbar */}
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shadow-md">
            <Heart className="w-6 h-6 fill-current" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 leading-none">
              AyuCare
            </h1>
            <p className="text-xs text-slate-500 font-medium mt-0.5 hidden sm:block">
              {t('app_tagline')}
            </p>
          </div>
        </div>

        {/* Middle: Active Role Status */}
        {badge && (
          <div className="hidden md:flex items-center gap-2">
            <span
              className={`px-3 py-1 rounded-full text-xs sm:text-sm font-bold border ${badge.bg} flex items-center gap-1.5`}
            >
              <UserCheck className="w-4 h-4" />
              {badge.label}
            </span>
            <span className="text-xs text-slate-500 font-semibold">
              Profile: <span className="text-slate-800 font-bold">{user.profile_name}</span>
            </span>
          </div>
        )}

        {/* Right Accessibility Controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Large Font Toggle */}
          <button
            onClick={toggleLargeFont}
            title="Toggle Extra Large Senior Font"
            className={`p-2 rounded-xl border flex items-center gap-1 transition ${
              largeFont
                ? 'bg-amber-100 border-amber-300 text-amber-900 font-bold'
                : 'bg-slate-100 border-slate-200 text-slate-700 hover:bg-slate-200'
            }`}
          >
            <Type className="w-5 h-5" />
            <span className="text-xs font-bold">{largeFont ? 'A+' : 'A'}</span>
          </button>

          {/* 3-Option Language Selector (English / தமிழ் / हिन्दी) */}
          <div className="flex items-center bg-slate-100 p-0.5 rounded-xl border border-slate-300">
            <Globe className="w-4 h-4 ml-2 mr-1 text-emerald-600 hidden lg:block" />
            {[
              { code: 'en', label: 'EN' },
              { code: 'ta', label: 'தமிழ்' },
              { code: 'hi', label: 'हिन्दी' }
            ].map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageSelect(lang.code)}
                className={`px-2 sm:px-2.5 py-1 rounded-lg font-bold text-xs sm:text-sm transition ${
                  i18n.language === lang.code
                    ? 'bg-emerald-600 text-white shadow-sm'
                    : 'text-slate-700 hover:text-slate-900 hover:bg-slate-200'
                }`}
                title={`Switch language to ${lang.label}`}
              >
                {lang.label}
              </button>
            ))}
          </div>

          {/* Logout */}
          <button
            onClick={logout}
            title={t('sign_out')}
            className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="bg-slate-50 border-t border-slate-200 overflow-x-auto">
        <div className="max-w-7xl mx-auto px-4 flex gap-1 sm:gap-2">
          {[
            { id: 'today', label: t('nav_today'), icon: '☀️' },
            { id: 'medications', label: t('nav_medications'), icon: '💊' },
            { id: 'approvals', label: t('nav_approvals'), icon: '🛡️' },
            { id: 'appointments', label: t('nav_appointments'), icon: '🩺' },
            { id: 'adherence', label: t('nav_adherence'), icon: '📊' },
            { id: 'activity', label: t('nav_activity'), icon: '📋' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id)}
              className={`py-3 px-3 sm:px-4 font-bold text-sm sm:text-base border-b-4 whitespace-nowrap transition flex items-center gap-2 ${
                currentTab === tab.id
                  ? 'border-emerald-600 text-emerald-700 bg-white shadow-sm'
                  : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </header>
  );
}
