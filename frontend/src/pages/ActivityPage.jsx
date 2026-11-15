import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  ListFilter,
  Clock,
  User,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  Heart,
  RefreshCw
} from 'lucide-react';

export default function ActivityPage() {
  const { t } = useTranslation();
  const { user, refreshTrigger } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, [refreshTrigger, user]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getActivityLogs(50);
      setLogs(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (action) => {
    if (action.includes('DOSE_TAKEN')) return { icon: <CheckCircle className="w-5 h-5 text-emerald-600" />, bg: 'bg-emerald-100' };
    if (action.includes('SOS')) return { icon: <AlertTriangle className="w-5 h-5 text-red-600" />, bg: 'bg-red-100' };
    if (action.includes('APPROVED')) return { icon: <ShieldCheck className="w-5 h-5 text-blue-600" />, bg: 'bg-blue-100' };
    if (action.includes('PROPOSED')) return { icon: <Clock className="w-5 h-5 text-amber-600" />, bg: 'bg-amber-100' };
    return { icon: <Heart className="w-5 h-5 text-purple-600" />, bg: 'bg-purple-100' };
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 shadow-xs border border-slate-200 flex items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {t('nav_activity')} ({logs.length})
          </h2>
          <p className="text-slate-500 font-medium text-sm mt-0.5">
            Full transparency log: who changed what, verified doses, and care alerts.
          </p>
        </div>

        <button
          onClick={fetchLogs}
          className="p-3 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-2xl transition"
          title="Refresh Log"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Activity Timeline */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-xs border border-slate-200 space-y-4">
        {logs.length === 0 ? (
          <p className="text-slate-500 text-center py-8">No activities recorded yet.</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {logs.map((log) => {
              const meta = getActionIcon(log.action);
              const dateStr = new Date(log.created_at).toLocaleString([], {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              });

              return (
                <div key={log.id} className="py-4 flex items-start gap-4">
                  <div className={`w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 ${meta.bg}`}>
                    {meta.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-900 text-sm sm:text-base leading-snug">
                      {log.details}
                    </p>
                    <div className="flex flex-wrap items-center gap-2 mt-1 text-xs text-slate-500 font-semibold">
                      <span className="flex items-center gap-1 text-slate-700">
                        <User className="w-3.5 h-3.5" />
                        <span className="font-bold">{log.performed_by_name}</span>
                      </span>
                      <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-800 text-[10px] font-extrabold uppercase border">
                        {log.performed_by_role}
                      </span>
                      <span>•</span>
                      <span>{dateStr}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
