import React, { useState } from 'react';
import { api } from '../api/client';
import { ShieldCheck, AlertTriangle, X, Search, Sparkles, Apple } from 'lucide-react';

export default function InteractionCheckerModal({ isOpen, onClose, currentMedicines = [] }) {
  const [medicineQuery, setMedicineQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleCheck = async (e) => {
    e?.preventDefault();
    if (!medicineQuery.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.checkDrugInteraction(medicineQuery.trim(), currentMedicines);
      setResult(res);
    } catch (err) {
      setError(err.message || 'Check failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'HIGH_RISK':
        return {
          bg: 'bg-red-100 text-red-900 border-red-300',
          title: 'High Caution / Adverse Risk Detected',
          icon: '🚨'
        };
      case 'CAUTION':
        return {
          bg: 'bg-amber-100 text-amber-900 border-amber-300',
          title: 'Moderate Caution Advised',
          icon: '⚠️'
        };
      default:
        return {
          bg: 'bg-emerald-100 text-emerald-900 border-emerald-300',
          title: 'No Severe Known Interactions Found',
          icon: '✅'
        };
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-3xl max-w-xl w-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl border border-slate-200 animate-scale-up">
        {/* Header */}
        <div className="bg-slate-900 text-white p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-500/20 flex items-center justify-center">
              <ShieldCheck className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <h2 className="text-xl font-black">AI Drug & Food Interaction Check</h2>
              <p className="text-xs text-slate-400 font-medium">Powered by Google Gemini Clinical Intelligence</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-slate-400 hover:text-white rounded-full transition">
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Currently Active Regimen */}
          <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
              Currently Active Medications in Regimen ({currentMedicines.length}):
            </p>
            <div className="flex flex-wrap gap-1.5">
              {currentMedicines.map((m, idx) => (
                <span
                  key={idx}
                  className="bg-white text-slate-800 text-xs font-bold px-2.5 py-1 rounded-lg border border-slate-200 shadow-xs"
                >
                  {m}
                </span>
              ))}
            </div>
          </div>

          {/* Search Form */}
          <form onSubmit={handleCheck} className="space-y-3">
            <label className="block text-sm font-bold text-slate-800">
              Check a new medication or supplement:
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={medicineQuery}
                onChange={(e) => setMedicineQuery(e.target.value)}
                placeholder="e.g. Aspirin, Ibuprofen, Atorvastatin, Grapefruit"
                className="flex-1 p-3.5 rounded-xl border-2 border-slate-200 focus:border-emerald-500 focus:outline-none text-slate-900 font-medium text-base"
              />
              <button
                type="submit"
                disabled={loading || !medicineQuery.trim()}
                className="px-6 py-3.5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-bold rounded-xl transition flex items-center gap-2 disabled:opacity-50"
              >
                <Search className="w-5 h-5" />
                <span>{loading ? 'Checking...' : 'Check'}</span>
              </button>
            </div>
          </form>

          {error && (
            <div className="p-3 bg-red-50 text-red-700 rounded-xl text-xs font-bold">
              {error}
            </div>
          )}

          {/* Results Display */}
          {result && (
            <div className="space-y-4 pt-2">
              {/* Overall Status Banner */}
              {(() => {
                const badge = getStatusBadge(result.overall_status);
                return (
                  <div className={`p-4 rounded-2xl border-2 ${badge.bg} flex items-center gap-3`}>
                    <span className="text-2xl">{badge.icon}</span>
                    <div>
                      <h4 className="font-black text-base">{badge.title}</h4>
                      <p className="text-xs font-medium opacity-90">
                        Evaluated against {currentMedicines.length} current prescriptions.
                      </p>
                    </div>
                  </div>
                );
              })()}

              {/* Specific Warnings */}
              {result.warnings?.length > 0 && (
                <div className="space-y-2">
                  <h5 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Interaction Details:
                  </h5>
                  {result.warnings.map((w, i) => (
                    <div
                      key={i}
                      className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl space-y-1"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-amber-950 text-sm">{w.title}</span>
                        <span className="text-xs font-black px-2 py-0.5 rounded bg-amber-200 text-amber-900">
                          {w.severity}
                        </span>
                      </div>
                      <p className="text-xs text-amber-900 leading-relaxed font-medium">
                        {w.description}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {/* Food & Dietary Advice */}
              {result.food_considerations?.length > 0 && (
                <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-2xl space-y-2">
                  <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm">
                    <Apple className="w-4 h-4 text-emerald-700" />
                    <span>Dietary & Food Precautions:</span>
                  </div>
                  <ul className="list-disc list-inside space-y-1 text-xs text-emerald-950 font-medium">
                    {result.food_considerations.map((tip, i) => (
                      <li key={i}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Mandatory Medical Disclaimer */}
              <div className="p-3 bg-slate-100 border border-slate-300 rounded-xl text-center">
                <p className="text-xs text-slate-600 font-semibold italic">
                  ⚖️ {result.disclaimer}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
