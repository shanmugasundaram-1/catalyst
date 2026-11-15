import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Mail, CheckCircle, Sparkles, X, Calendar, Activity, Globe } from 'lucide-react';

export default function WeeklySummaryModal({ isOpen, onClose }) {
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [emailSending, setEmailSending] = useState(false);
  const [emailSentSuccess, setEmailSentSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadSummary();
    } else {
      setSummary(null);
      setEmailSentSuccess(false);
    }
  }, [isOpen]);

  const loadSummary = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getWeeklySummary(false);
      setSummary(data);
    } catch (err) {
      setError(err.message || 'Failed to load weekly summary');
    } finally {
      setLoading(false);
    }
  };

  const handleSendEmail = async () => {
    setEmailSending(true);
    try {
      await api.getWeeklySummary(true);
      setEmailSentSuccess(true);
    } catch (err) {
      setError(err.message || 'Failed to dispatch email');
    } finally {
      setEmailSending(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl border border-slate-200 animate-scale-up">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-amber-300" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-black">AI Weekly Family Summary</h2>
              <p className="text-blue-100 text-xs sm:text-sm font-medium">
                Empathetic care digest in English, தமிழ் & हिन्दी
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-white hover:bg-white/20 rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {loading && (
            <div className="text-center py-12 space-y-3">
              <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-sm font-bold text-slate-600">Generating empathetic family summary with Gemini...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-50 text-red-700 rounded-xl text-sm font-bold">
              {error}
            </div>
          )}

          {summary && !loading && (
            <div className="space-y-6">
              {/* Quick KPI stats */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-emerald-50 border border-emerald-200 p-3.5 rounded-2xl text-center">
                  <span className="text-xs font-bold text-emerald-800 uppercase block">Adherence</span>
                  <span className="text-2xl font-black text-emerald-700">{summary.adherence_percentage}%</span>
                </div>
                <div className="bg-blue-50 border border-blue-200 p-3.5 rounded-2xl text-center">
                  <span className="text-xs font-bold text-blue-800 uppercase block">Doses Taken</span>
                  <span className="text-2xl font-black text-blue-700">{summary.taken_count}</span>
                </div>
                <div className="bg-amber-50 border border-amber-200 p-3.5 rounded-2xl text-center">
                  <span className="text-xs font-bold text-amber-800 uppercase block">Missed</span>
                  <span className="text-2xl font-black text-amber-700">{summary.missed_count}</span>
                </div>
              </div>

              {/* English Summary */}
              <div className="bg-slate-50 border-2 border-slate-200 rounded-2xl p-5 space-y-2">
                <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-slate-500">
                  <Globe className="w-4 h-4 text-blue-600" />
                  <span>English Summary for Family Circle</span>
                </div>
                <p className="text-slate-900 font-medium text-base leading-relaxed">
                  "{summary.friendly_summary_en}"
                </p>
              </div>

              {/* Tamil Summary */}
              <div className="bg-emerald-50/50 border-2 border-emerald-200 rounded-2xl p-5 space-y-2">
                <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-emerald-800">
                  <Globe className="w-4 h-4 text-emerald-600" />
                  <span>தமிழ் வடிவம் (Tamil Summary)</span>
                </div>
                <p className="text-slate-900 font-medium text-base leading-relaxed">
                  "{summary.friendly_summary_ta}"
                </p>
              </div>

              {/* Hindi Summary */}
              {summary.friendly_summary_hi && (
                <div className="bg-amber-50/50 border-2 border-amber-200 rounded-2xl p-5 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-amber-800">
                    <Globe className="w-4 h-4 text-amber-600" />
                    <span>हिन्दी सारांश (Hindi Summary for Family)</span>
                  </div>
                  <p className="text-slate-900 font-medium text-base leading-relaxed">
                    "{summary.friendly_summary_hi}"
                  </p>
                </div>
              )}

              {/* Upcoming Appointments */}
              {summary.upcoming_appointments?.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Upcoming Doctor Consultations:
                  </span>
                  <div className="space-y-1.5">
                    {summary.upcoming_appointments.map((appt, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm font-semibold text-slate-800 bg-slate-100 p-2.5 rounded-xl border border-slate-200">
                        <Calendar className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        <span>{appt}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Action: Send email to family */}
              <div className="pt-2">
                {emailSentSuccess ? (
                  <div className="p-4 bg-emerald-100 text-emerald-900 rounded-2xl font-bold text-center flex items-center justify-center gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-700" />
                    <span>Weekly Summary successfully emailed to all family members!</span>
                  </div>
                ) : (
                  <button
                    onClick={handleSendEmail}
                    disabled={emailSending}
                    className="w-full py-4 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white font-black text-base rounded-2xl shadow-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    <Mail className="w-5 h-5" />
                    <span>{emailSending ? 'Sending emails...' : 'Email This Summary to Family Circle'}</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
