import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import ElderDoseCard from '../components/ElderDoseCard';
import CareInsightsCard from '../components/CareInsightsCard';
import {
  Calendar,
  CheckCircle2,
  Clock,
  Sparkles,
  ShieldCheck,
  Flame,
  Award,
  AlertTriangle,
  ChevronRight,
  Utensils,
  Mic
} from 'lucide-react';

export default function TodayPage({ onOpenAI, onOpenSafety, onOpenSummary, onOpenVoice, onNavigate }) {
  const { t, i18n } = useTranslation();
  const { user, refreshTrigger } = useAuth();
  const [overview, setOverview] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  const isElderOrCaretaker = user?.role === 'ELDER' || user?.role === 'CARETAKER';

  useEffect(() => {
    fetchTodayData();
  }, [refreshTrigger, user]);

  const fetchTodayData = async () => {
    setLoading(true);
    try {
      const data = await api.getTodayOverview();
      setOverview(data);
      const appts = await api.listAppointments(true);
      setAppointments(appts || []);
    } catch (err) {
      console.error('Error fetching today overview:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTakeDose = async (doseId) => {
    try {
      await api.recordDoseAction(doseId, 'TAKEN');
      fetchTodayData();
    } catch (err) {
      alert(err.message || 'Failed to update dose');
    }
  };

  const handleStatusChange = async (doseId, newStatus) => {
    try {
      await api.recordDoseAction(doseId, newStatus);
      fetchTodayData();
    } catch (err) {
      alert(err.message || 'Failed to change status');
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Elder Greeting Banner */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 shadow-xs border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs sm:text-sm font-bold text-slate-400 uppercase tracking-wider">
            {new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
          </span>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight mt-0.5">
            Vanakkam, {user?.profile_name || 'Sundaram'}! 🌸
          </h2>
          <p className="text-slate-600 font-medium text-sm sm:text-base mt-1">
            Keeping you at the center of your healthcare decisions every day.
          </p>
        </div>

        {/* Quick KPI badges */}
        <div className="flex items-center gap-3 self-start md:self-auto">
          {/* Adherence Streak */}
          <div className="bg-amber-50 border-2 border-amber-200 px-4 py-2.5 rounded-2xl flex items-center gap-2.5">
            <Flame className="w-7 h-7 text-amber-500 fill-amber-500" />
            <div>
              <span className="text-xl font-black text-amber-900 leading-none block">
                {overview?.streak_days || 0} {t('days')}
              </span>
              <span className="text-xs font-bold text-amber-700">{t('streak_label')}</span>
            </div>
          </div>

          {/* Adherence % */}
          <div className="bg-emerald-50 border-2 border-emerald-200 px-4 py-2.5 rounded-2xl flex items-center gap-2.5">
            <Award className="w-7 h-7 text-emerald-600" />
            <div>
              <span className="text-xl font-black text-emerald-900 leading-none block">
                {overview?.adherence_percentage || 100}%
              </span>
              <span className="text-xs font-bold text-emerald-700">{t('adherence_rate')}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Voice-First Assistant Action Card for Elder */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-700 rounded-3xl p-5 sm:p-6 text-white shadow-md flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3.5 text-center sm:text-left">
          <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center flex-shrink-0 mx-auto sm:mx-0">
            <Mic className="w-6 h-6 text-white animate-pulse" />
          </div>
          <div>
            <h3 className="text-xl font-black leading-tight">
              {t('voice_assistant')} ({i18n.language === 'hi' ? 'हिन्दी' : i18n.language === 'ta' ? 'தமிழ்' : 'English'})
            </h3>
            <p className="text-emerald-100 text-xs sm:text-sm font-medium mt-0.5">
              {i18n.language === 'hi'
                ? 'बोलकर दवा दर्ज करें, अगली खुराक पूछें या अपॉइंटमेंट जांचें'
                : i18n.language === 'ta'
                ? 'குரல் மூலம் மாத்திரை பதிவு செய்ய அல்லது நேரம் கேட்க தட்டவும்'
                : 'Speak to record doses taken, check next medicine, or query appointments'}
            </p>
          </div>
        </div>

        <button
          onClick={onOpenVoice}
          className="w-full sm:w-auto px-6 py-3 bg-white hover:bg-emerald-50 text-emerald-900 rounded-2xl font-black text-sm sm:text-base shadow-lg transition active:scale-95 flex items-center justify-center gap-2 cursor-pointer flex-shrink-0"
        >
          <Mic className="w-5 h-5 text-emerald-700" />
          <span>{t('voice_tap_to_speak')}</span>
        </button>
      </div>

      {/* CORE ELDER NEXT DOSE CARD */}
      <ElderDoseCard
        nextDose={overview?.next_dose}
        onTakeDose={handleTakeDose}
        isElderOrCaretaker={isElderOrCaretaker}
      />

      {/* AI EARLY WARNING & CARE INSIGHTS CARD */}
      <CareInsightsCard />

      {/* Quick AI & Care Tool Shortcuts */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        <button
          onClick={onOpenAI}
          className="p-5 bg-gradient-to-br from-emerald-50 to-teal-50 hover:from-emerald-100 hover:to-teal-100 border-2 border-emerald-200 rounded-3xl text-left transition flex items-center gap-4 group cursor-pointer shadow-xs"
        >
          <div className="w-12 h-12 rounded-2xl bg-emerald-600 text-white flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition shadow-sm">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h4 className="font-black text-slate-900 text-base">Scan Prescription</h4>
            <p className="text-xs text-slate-600 font-medium">Gemini Vision photo scanner</p>
          </div>
        </button>

        <button
          onClick={onOpenSafety}
          className="p-5 bg-gradient-to-br from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 border-2 border-blue-200 rounded-3xl text-left transition flex items-center gap-4 group cursor-pointer shadow-xs"
        >
          <div className="w-12 h-12 rounded-2xl bg-blue-600 text-white flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition shadow-sm">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h4 className="font-black text-slate-900 text-base">Safety & Food Check</h4>
            <p className="text-xs text-slate-600 font-medium">Drug & diet warning analysis</p>
          </div>
        </button>

        <button
          onClick={onOpenSummary}
          className="p-5 bg-gradient-to-br from-purple-50 to-fuchsia-50 hover:from-purple-100 hover:to-fuchsia-100 border-2 border-purple-200 rounded-3xl text-left transition flex items-center gap-4 group cursor-pointer shadow-xs"
        >
          <div className="w-12 h-12 rounded-2xl bg-purple-600 text-white flex items-center justify-center flex-shrink-0 group-hover:scale-105 transition shadow-sm">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <h4 className="font-black text-slate-900 text-base">Family Weekly Digest</h4>
            <p className="text-xs text-slate-600 font-medium">AI summary in English & Tamil</p>
          </div>
        </button>
      </div>

      {/* TODAY'S FULL DOSE TIMELINE */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-xs border border-slate-200 space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <Clock className="w-6 h-6 text-emerald-600" />
            <h3 className="text-xl sm:text-2xl font-black text-slate-900">
              {t('all_doses_today')} ({overview?.today_doses?.length || 0})
            </h3>
          </div>
          <span className="text-xs font-bold text-slate-500">
            {overview?.total_taken || 0} Taken • {overview?.total_missed || 0} Missed
          </span>
        </div>

        {overview?.today_doses?.length === 0 ? (
          <p className="text-slate-500 text-center py-6 font-medium">No medications scheduled for today.</p>
        ) : (
          <div className="space-y-3">
            {overview?.today_doses?.map((dose) => {
              const time = new Date(dose.scheduled_time).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              });

              const isTaken = dose.status === 'TAKEN';
              const isMissed = dose.status === 'MISSED';
              const isPending = dose.status === 'PENDING';

              return (
                <div
                  key={dose.id}
                  className={`p-4 sm:p-5 rounded-2xl border-2 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                    isTaken
                      ? 'bg-emerald-50/60 border-emerald-300'
                      : isMissed
                      ? 'bg-red-50/60 border-red-300'
                      : 'bg-white border-slate-200'
                  }`}
                >
                  <div className="flex items-start gap-3 sm:gap-4">
                    <div
                      className={`w-11 h-11 rounded-2xl flex items-center justify-center font-bold text-sm flex-shrink-0 ${
                        isTaken
                          ? 'bg-emerald-500 text-white'
                          : isMissed
                          ? 'bg-red-500 text-white'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {time}
                    </div>
                    <div>
                      <h4 className="text-lg sm:text-xl font-black text-slate-950">
                        {dose.medication_name}
                      </h4>
                      <div className="flex flex-wrap items-center gap-2 mt-1">
                        <span className="text-sm font-bold text-emerald-800">
                          {dose.dosage}
                        </span>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border">
                          {dose.food_timing.replace('_', ' ')}
                        </span>
                        {dose.taken_by_name && (
                          <span className="text-xs font-medium text-emerald-700 italic">
                            ✓ Verified by {dose.taken_by_name}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Dose Status / Action Toggles */}
                  {isElderOrCaretaker && (
                    <div className="flex items-center gap-2 self-end sm:self-auto">
                      <button
                        onClick={() => handleStatusChange(dose.id, 'TAKEN')}
                        className={`px-3.5 py-1.5 rounded-xl font-bold text-xs sm:text-sm transition flex items-center gap-1.5 ${
                          isTaken
                            ? 'bg-emerald-600 text-white shadow-xs'
                            : 'bg-slate-100 text-slate-700 hover:bg-emerald-100 hover:text-emerald-800'
                        }`}
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        <span>Taken</span>
                      </button>
                      <button
                        onClick={() => handleStatusChange(dose.id, 'MISSED')}
                        className={`px-3.5 py-1.5 rounded-xl font-bold text-xs sm:text-sm transition ${
                          isMissed
                            ? 'bg-red-600 text-white shadow-xs'
                            : 'bg-slate-100 text-slate-700 hover:bg-red-100 hover:text-red-800'
                        }`}
                      >
                        Missed
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Upcoming Doctor Visit Reminder */}
      {appointments.length > 0 && (
        <div className="bg-gradient-to-r from-teal-700 to-emerald-800 rounded-3xl p-6 sm:p-7 text-white shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center flex-shrink-0">
              <Calendar className="w-7 h-7 text-amber-300" />
            </div>
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-teal-200">
                Upcoming Doctor Visit
              </span>
              <h4 className="text-xl sm:text-2xl font-black text-white">
                Dr. {appointments[0].doctor_name} ({appointments[0].specialty})
              </h4>
              <p className="text-sm text-teal-100 font-medium">
                {new Date(appointments[0].appointment_time).toLocaleString([], {
                  weekday: 'short',
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}{' '}
                • {appointments[0].location}
              </p>
            </div>
          </div>
          <button
            onClick={() => onNavigate('appointments')}
            className="px-5 py-2.5 bg-white text-teal-900 hover:bg-teal-50 font-black text-sm rounded-xl transition flex items-center gap-1 self-start sm:self-auto"
          >
            <span>View All</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}
