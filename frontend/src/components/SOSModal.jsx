import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import { ShieldAlert, X, PhoneCall, CheckCircle, AlertTriangle } from 'lucide-react';

export default function SOSModal({ isOpen, onClose, elderName, emergencyPhone, onTriggered }) {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSendSOS = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.triggerSOS('Emergency SOS triggered from AyuCare Home Screen');
      setResult(res);
      if (onTriggered) onTriggered();
    } catch (err) {
      setError(err.message || 'Failed to dispatch SOS alert');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-3xl max-w-lg w-full overflow-hidden shadow-2xl border-4 border-red-600 animate-scale-up">
        {/* Header */}
        <div className="bg-red-600 text-white p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-9 h-9 animate-bounce" />
            <div>
              <h2 className="text-2xl sm:text-3xl font-black uppercase tracking-wide">
                {t('emergency_sos')}
              </h2>
              <p className="text-red-100 text-sm font-semibold">Immediate Care Circle Alert</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-white hover:bg-red-700 rounded-full transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 sm:p-8 space-y-6">
          {!result ? (
            <>
              <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-5 text-red-950">
                <p className="text-lg font-bold leading-relaxed">
                  Pressing this button will <span className="underline font-black">immediately send an urgent high-priority emergency broadcast</span> to your caretaker and family members via email and instant notifications.
                </p>
              </div>

              <div className="space-y-3 bg-slate-50 p-4 rounded-2xl border border-slate-200">
                <div className="flex justify-between items-center text-sm font-semibold text-slate-700">
                  <span>Elder in Need:</span>
                  <span className="font-bold text-slate-950 text-base">{elderName}</span>
                </div>
                <div className="flex justify-between items-center text-sm font-semibold text-slate-700">
                  <span>Emergency Phone:</span>
                  <a
                    href={`tel:${emergencyPhone}`}
                    className="font-bold text-emerald-700 flex items-center gap-1 hover:underline text-base"
                  >
                    <PhoneCall className="w-4 h-4" />
                    {emergencyPhone || 'Not configured'}
                  </a>
                </div>
              </div>

              {error && (
                <div className="p-4 bg-red-100 border border-red-300 text-red-800 rounded-xl text-sm font-bold flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="flex-1 py-4 px-6 rounded-2xl font-bold text-slate-700 bg-slate-200 hover:bg-slate-300 text-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSendSOS}
                  disabled={loading}
                  className="flex-1 py-4 px-6 rounded-2xl font-black text-white bg-red-600 hover:bg-red-700 active:scale-95 text-lg shadow-xl shadow-red-600/30 flex items-center justify-center gap-2 transition disabled:opacity-50 cursor-pointer"
                >
                  <ShieldAlert className="w-6 h-6" />
                  <span>{loading ? 'Alerting...' : 'SEND SOS NOW'}</span>
                </button>
              </div>
            </>
          ) : (
            <div className="text-center py-4 space-y-4">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="w-10 h-10" />
              </div>
              <h3 className="text-2xl font-black text-slate-900">
                Emergency Alert Dispatched!
              </h3>
              <p className="text-slate-600 font-medium">
                {result.message}
              </p>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-left text-xs font-semibold text-slate-700 space-y-1">
                <div className="font-bold text-slate-900 mb-1">Recipients Alerted:</div>
                {result.recipients_notified.map((email, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-emerald-700 font-mono">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    <span>{email}</span>
                  </div>
                ))}
              </div>
              <button
                onClick={onClose}
                className="w-full py-3.5 bg-slate-900 text-white font-bold rounded-xl text-base hover:bg-slate-800 transition"
              >
                Close Alert Window
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
