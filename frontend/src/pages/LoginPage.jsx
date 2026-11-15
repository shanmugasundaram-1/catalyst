import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  Heart,
  KeyRound,
  ShieldCheck,
  User,
  Mail,
  Sparkles,
  ArrowRight,
  AlertCircle,
  PlusCircle
} from 'lucide-react';

export default function LoginPage() {
  const { t, i18n } = useTranslation();
  const { loginWithPasscode, changeLanguage } = useAuth();

  const [isRegistering, setIsRegistering] = useState(false);
  const [profileId, setProfileId] = useState('DEMO-ELDER');
  const [passcode, setPasscode] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Register state
  const [regFullName, setRegFullName] = useState('');
  const [regAge, setRegAge] = useState(72);
  const [regElderPasscode, setRegElderPasscode] = useState('1111');
  const [regCaretakerPasscode, setRegCaretakerPasscode] = useState('2222');
  const [regFamilyPasscode, setRegFamilyPasscode] = useState('3333');
  const [regCreatorEmail, setRegCreatorEmail] = useState('');

  const handleJoin = async (e) => {
    e?.preventDefault();
    if (!profileId || !passcode || !name || !email) {
      setError('Please fill in all fields.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await loginWithPasscode({
        profile_id: profileId.trim(),
        passcode: passcode.trim(),
        name: name.trim(),
        email: email.trim()
      });
    } catch (err) {
      setError(err.message || 'Passcode login failed. Please check the passcode.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = async (role) => {
    const demos = {
      ELDER: { code: '1111', name: 'Sundaram Raman (Elder)', email: 'sundaram@ayucare.demo', lang: 'ta' },
      CARETAKER: { code: '2222', name: 'Priya (Nurse Caretaker)', email: 'priya.care@ayucare.demo', lang: 'en' },
      FAMILY: { code: '3333', name: 'Karthik Sundaram (Son)', email: 'karthik.family@ayucare.demo', lang: 'hi' }
    };
    const c = demos[role];
    setProfileId('DEMO-ELDER');
    setPasscode(c.code);
    setName(c.name);
    setEmail(c.email);

    setLoading(true);
    setError('');
    try {
      await loginWithPasscode({
        profile_id: 'DEMO-ELDER',
        passcode: c.code,
        name: c.name,
        email: c.email,
        language: c.lang
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!regFullName || !regCreatorEmail) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.registerProfile({
        full_name: regFullName,
        age: parseInt(regAge, 10) || 72,
        elder_passcode: regElderPasscode,
        caretaker_passcode: regCaretakerPasscode,
        family_passcode: regFamilyPasscode,
        creator_name: regFullName,
        creator_email: regCreatorEmail,
        emergency_phone: '+91 98401 23456'
      });
      // Automatically join with the returned profile
      await loginWithPasscode({
        profile_id: res.profile_id,
        passcode: regElderPasscode,
        name: regFullName,
        email: regCreatorEmail
      });
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-teal-950 flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full space-y-6">
        {/* Language selector for Login screen */}
        <div className="flex justify-end">
          <div className="flex items-center bg-white/10 backdrop-blur-md p-1 rounded-xl border border-white/20">
            {[
              { code: 'en', label: 'English' },
              { code: 'ta', label: 'தமிழ்' },
              { code: 'hi', label: 'हिन्दी' }
            ].map((lang) => (
              <button
                key={lang.code}
                onClick={() => {
                  i18n.changeLanguage(lang.code);
                  localStorage.setItem('ayucare_lang', lang.code);
                }}
                className={`px-3 py-1 rounded-lg font-bold text-xs transition ${
                  i18n.language === lang.code
                    ? 'bg-emerald-500 text-white shadow-md'
                    : 'text-slate-300 hover:text-white hover:bg-white/10'
                }`}
              >
                {lang.label}
              </button>
            ))}
          </div>
        </div>

        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-white mx-auto shadow-xl">
            <Heart className="w-9 h-9 fill-current" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
            AyuCare
          </h1>
          <p className="text-teal-200 text-sm font-medium">
            Keeping the elderly person at the center of their healthcare decisions.
          </p>
        </div>

        {/* 1-Click Quick Demo Sign-in for Judges */}
        <div className="bg-white/10 backdrop-blur-md rounded-3xl p-5 border border-white/20 text-white space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-amber-300" />
            <span className="text-xs font-black uppercase tracking-wider text-amber-300">
              1-Click Demo Sign-in (PromptWars Hackathon)
            </span>
          </div>
          <p className="text-xs text-slate-300 font-medium">
            Select a role below to test the passcode-based permissions immediately:
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => handleQuickDemo('ELDER')}
              className="p-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-black text-xs transition shadow-md flex flex-col items-center text-center gap-1 cursor-pointer"
            >
              <span className="text-base">👴</span>
              <span>Elder</span>
              <span className="text-[10px] font-mono text-emerald-200">Pass: 1111</span>
            </button>
            <button
              onClick={() => handleQuickDemo('CARETAKER')}
              className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 font-black text-xs transition shadow-md flex flex-col items-center text-center gap-1 cursor-pointer"
            >
              <span className="text-base">🩺</span>
              <span>Caretaker</span>
              <span className="text-[10px] font-mono text-blue-200">Pass: 2222</span>
            </button>
            <button
              onClick={() => handleQuickDemo('FAMILY')}
              className="p-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 font-black text-xs transition shadow-md flex flex-col items-center text-center gap-1 cursor-pointer"
            >
              <span className="text-base">👨‍👩‍👧</span>
              <span>Family</span>
              <span className="text-[10px] font-mono text-purple-200">Pass: 3333</span>
            </button>
          </div>
        </div>

        {/* Main Card: Join or Register */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-2xl space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h2 className="text-xl font-black text-slate-900">
              {isRegistering ? 'Create Elder Profile' : 'Join Profile by Passcode'}
            </h2>
            <button
              onClick={() => {
                setIsRegistering(!isRegistering);
                setError('');
              }}
              className="text-xs font-bold text-emerald-700 hover:underline"
            >
              {isRegistering ? 'Existing Profile?' : '+ New Profile'}
            </button>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs font-bold flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!isRegistering ? (
            <form onSubmit={handleJoin} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Elder Profile ID
                </label>
                <input
                  type="text"
                  required
                  value={profileId}
                  onChange={(e) => setProfileId(e.target.value)}
                  placeholder="e.g. DEMO-ELDER"
                  className="w-full p-3 rounded-xl border border-slate-300 font-bold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">
                  Role Passcode (Decides your role)
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                  <input
                    type="password"
                    required
                    value={passcode}
                    onChange={(e) => setPasscode(e.target.value)}
                    placeholder="Enter 4-digit passcode (1111, 2222, 3333)"
                    className="w-full pl-10 pr-3 py-3 rounded-xl border border-slate-300 font-bold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">Your Name</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Sundaram"
                    className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1">Your Email</label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="alerts@email.com"
                    className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-black rounded-xl text-base shadow-lg transition flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
              >
                <span>{loading ? 'Verifying Passcode...' : 'Enter Profile'}</span>
                <ArrowRight className="w-5 h-5" />
              </button>
            </form>
          ) : (
            <form onSubmit={handleRegister} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">Elder Full Name</label>
                <input
                  type="text"
                  required
                  value={regFullName}
                  onChange={(e) => setRegFullName(e.target.value)}
                  placeholder="e.g. Sundaram Raman"
                  className="w-full p-2.5 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">Notification Email</label>
                <input
                  type="email"
                  required
                  value={regCreatorEmail}
                  onChange={(e) => setRegCreatorEmail(e.target.value)}
                  placeholder="sundaram@ayucare.org"
                  className="w-full p-2.5 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 mb-1">Elder Pass</label>
                  <input
                    type="text"
                    value={regElderPasscode}
                    onChange={(e) => setRegElderPasscode(e.target.value)}
                    className="w-full p-2 rounded-lg border font-mono text-center text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 mb-1">Caretaker Pass</label>
                  <input
                    type="text"
                    value={regCaretakerPasscode}
                    onChange={(e) => setRegCaretakerPasscode(e.target.value)}
                    className="w-full p-2 rounded-lg border font-mono text-center text-xs"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 mb-1">Family Pass</label>
                  <input
                    type="text"
                    value={regFamilyPasscode}
                    onChange={(e) => setRegFamilyPasscode(e.target.value)}
                    className="w-full p-2 rounded-lg border font-mono text-center text-xs"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-black rounded-xl text-sm transition mt-2 cursor-pointer"
              >
                {loading ? 'Creating...' : 'Register & Enter'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
