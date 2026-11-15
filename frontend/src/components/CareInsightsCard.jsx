import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  Lightbulb,
  AlertTriangle,
  AlertOctagon,
  Info,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  RefreshCw
} from 'lucide-react';

export default function CareInsightsCard() {
  const { t, i18n } = useTranslation();
  const { user, refreshTrigger } = useAuth();
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    fetchInsights();
  }, [refreshTrigger, user]);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const data = await api.getInsights(10);
      setInsights(data || []);
    } catch (err) {
      console.warn('Failed to fetch care insights:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (id) => {
    try {
      await api.markInsightSeen(id);
      setInsights((prev) =>
        prev.map((ins) => (ins.id === id ? { ...ins, status: 'SEEN' } : ins))
      );
    } catch (err) {
      console.error('Failed to acknowledge insight:', err);
    }
  };

  const handleRunScan = async () => {
    setAnalyzing(true);
    try {
      await api.analyzeInsightsNow();
      await fetchInsights();
    } catch (err) {
      console.error('Failed to run on-demand analysis:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  // Helper to get localized field
  const getLocalizedField = (ins, field) => {
    const lang = i18n.language;
    if (field === 'title') {
      return (lang === 'hi' ? ins.title_hi : lang === 'ta' ? ins.title_ta : ins.title_en) || ins.title_en;
    }
    if (field === 'text') {
      return (lang === 'hi' ? ins.text_hi : lang === 'ta' ? ins.text_ta : ins.text_en) || ins.text_en;
    }
    if (field === 'action') {
      return (lang === 'hi' ? ins.suggested_action_hi : lang === 'ta' ? ins.suggested_action_ta : ins.suggested_action) || ins.suggested_action;
    }
    return '';
  };

  const getSeverityBadge = (severity) => {
    switch (severity) {
      case 'urgent':
        return {
          icon: <AlertOctagon className="w-5 h-5 text-red-600" />,
          cardBg: 'bg-red-50/70 border-red-300',
          badgeBg: 'bg-red-100 text-red-800 border-red-300',
          label: 'URGENT'
        };
      case 'warning':
        return {
          icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
          cardBg: 'bg-amber-50/70 border-amber-300',
          badgeBg: 'bg-amber-100 text-amber-800 border-amber-300',
          label: 'WARNING'
        };
      default:
        return {
          icon: <Info className="w-5 h-5 text-blue-600" />,
          cardBg: 'bg-blue-50/70 border-blue-300',
          badgeBg: 'bg-blue-100 text-blue-800 border-blue-300',
          label: 'INFO'
        };
    }
  };

  return (
    <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-xs border border-slate-200 space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
            <Lightbulb className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl sm:text-2xl font-black text-slate-900 leading-tight">
              {t('insights_title')}
            </h3>
            <p className="text-xs sm:text-sm text-slate-500 font-medium">
              {t('insights_subtitle')}
            </p>
          </div>
        </div>

        {/* Trigger analysis shortcut */}
        <button
          onClick={handleRunScan}
          disabled={analyzing}
          className="self-start sm:self-auto px-3.5 py-1.5 rounded-xl border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center gap-2 transition disabled:opacity-50 cursor-pointer"
          title="Run 14-day analysis now"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin text-emerald-600' : ''}`} />
          <span>{analyzing ? 'Scanning...' : t('insights_analyze_btn')}</span>
        </button>
      </div>

      {/* Insights List */}
      {loading ? (
        <div className="text-center py-6 text-slate-400 font-medium text-sm">
          Loading health pattern insights...
        </div>
      ) : insights.length === 0 ? (
        <div className="p-6 bg-slate-50 rounded-2xl border border-slate-200 text-center">
          <ShieldCheck className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
          <p className="font-bold text-slate-800 text-base">
            {t('insights_no_alerts')}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            No repeated dose misses, stock shortages, or adherence drops detected in the last 14 days.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {insights.map((ins) => {
            const badge = getSeverityBadge(ins.severity);
            const isSeen = ins.status === 'SEEN';
            const title = getLocalizedField(ins, 'title');
            const text = getLocalizedField(ins, 'text');
            const action = getLocalizedField(ins, 'action');

            return (
              <div
                key={ins.id}
                className={`p-5 rounded-2xl border-2 transition ${badge.cardBg} ${
                  isSeen ? 'opacity-70' : 'shadow-xs'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2.5">
                    {badge.icon}
                    <h4 className="text-lg font-black text-slate-900 leading-snug">
                      {title}
                    </h4>
                  </div>
                  <div className="flex items-center gap-2 self-start sm:self-auto">
                    <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-black border ${badge.badgeBg}`}>
                      {badge.label}
                    </span>
                    <span className="text-[11px] text-slate-500 font-semibold">
                      {new Date(ins.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <p className="text-slate-800 text-sm sm:text-base font-medium leading-relaxed my-2">
                  {text}
                </p>

                {action && (
                  <div className="mt-3 p-3 bg-white/80 rounded-xl border border-slate-200 flex items-start gap-2 text-xs sm:text-sm font-bold text-slate-900">
                    <Sparkles className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                    <span>
                      <span className="text-slate-500 uppercase tracking-wider text-[11px] mr-1 block sm:inline">
                        {t('insights_suggested_action')}:
                      </span>
                      {action}
                    </span>
                  </div>
                )}

                <div className="mt-4 flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-200/60">
                  <span className="text-[11px] text-slate-500 italic">
                    ⚠️ {t('insights_medical_disclaimer')}
                  </span>

                  {isSeen ? (
                    <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-700">
                      <CheckCircle2 className="w-4 h-4" />
                      {t('insights_acknowledged')}
                    </span>
                  ) : (
                    <button
                      onClick={() => handleAcknowledge(ins.id)}
                      className="px-3.5 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer"
                    >
                      <span>{t('insights_mark_seen')}</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
