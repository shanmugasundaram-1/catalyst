import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  LineChart,
  Line,
  CartesianGrid
} from 'recharts';
import {
  Activity,
  Flame,
  Award,
  AlertCircle,
  TrendingUp,
  CheckCircle2,
  Calendar
} from 'lucide-react';

export default function AdherencePage() {
  const { t } = useTranslation();
  const { user, refreshTrigger } = useAuth();
  const [daysRange, setDaysRange] = useState(7);
  const [historyData, setHistoryData] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, [daysRange, refreshTrigger, user]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getDoseHistory(daysRange);
      setHistoryData(data.history || []);
      setSummary(data.summary || {});
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 shadow-xs border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {t('nav_adherence')}
          </h2>
          <p className="text-slate-500 font-medium text-sm mt-0.5">
            Real-time adherence analytics, daily compliance tracking, and streaks.
          </p>
        </div>

        {/* Range Selector */}
        <div className="flex bg-slate-100 p-1.5 rounded-2xl border border-slate-200 self-start sm:self-auto">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDaysRange(d)}
              className={`px-4 py-1.5 rounded-xl font-bold text-xs sm:text-sm transition ${
                daysRange === d
                  ? 'bg-white text-emerald-800 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {d} Days
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
        <div className="bg-white rounded-3xl p-5 border-2 border-emerald-200 shadow-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Adherence</span>
            <Award className="w-5 h-5 text-emerald-600" />
          </div>
          <span className="text-3xl sm:text-4xl font-black text-emerald-700 block">
            {summary?.adherence_percentage || 100}%
          </span>
          <span className="text-xs text-slate-500 font-medium block">Last {daysRange} days</span>
        </div>

        <div className="bg-white rounded-3xl p-5 border-2 border-amber-200 shadow-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Current Streak</span>
            <Flame className="w-5 h-5 text-amber-500 fill-amber-500" />
          </div>
          <span className="text-3xl sm:text-4xl font-black text-amber-900 block">
            {summary?.streak_days || 0} Days
          </span>
          <span className="text-xs text-slate-500 font-medium block">Consecutive perfect days</span>
        </div>

        <div className="bg-white rounded-3xl p-5 border-2 border-blue-200 shadow-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Doses Taken</span>
            <CheckCircle2 className="w-5 h-5 text-blue-600" />
          </div>
          <span className="text-3xl sm:text-4xl font-black text-blue-800 block">
            {summary?.total_taken || 0}
          </span>
          <span className="text-xs text-slate-500 font-medium block">Successfully recorded</span>
        </div>

        <div className="bg-white rounded-3xl p-5 border-2 border-red-200 shadow-xs space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-500 uppercase">Missed Doses</span>
            <AlertCircle className="w-5 h-5 text-red-600" />
          </div>
          <span className="text-3xl sm:text-4xl font-black text-red-700 block">
            {summary?.total_missed || 0}
          </span>
          <span className="text-xs text-slate-500 font-medium block">Escalated to care circle</span>
        </div>
      </div>

      {/* Chart 1: Taken vs Missed Bar Chart */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-xs border border-slate-200 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-black text-slate-900">Daily Medication Fulfillment</h3>
            <p className="text-xs text-slate-500 font-medium">Taken vs Missed count per day</p>
          </div>
        </div>

        <div className="h-72 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} />
              <YAxis stroke="#94a3b8" fontSize={12} allowDecimals={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  color: '#fff',
                  borderRadius: '12px',
                  border: 'none',
                  fontSize: '12px',
                  fontWeight: 'bold'
                }}
              />
              <Legend />
              <Bar dataKey="taken" name="Taken on Time" fill="#10b981" radius={[6, 6, 0, 0]} />
              <Bar dataKey="missed" name="Missed Dose" fill="#ef4444" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 2: Adherence Trend Line */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-xs border border-slate-200 space-y-4">
        <div>
          <h3 className="text-xl font-black text-slate-900">Adherence Percentage Trend</h3>
          <p className="text-xs text-slate-500 font-medium">Daily compliance target: &gt; 90%</p>
        </div>

        <div className="h-64 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={historyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} tickLine={false} />
              <YAxis domain={[0, 100]} stroke="#94a3b8" fontSize={12} tickLine={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  color: '#fff',
                  borderRadius: '12px',
                  border: 'none',
                  fontSize: '12px',
                  fontWeight: 'bold'
                }}
                formatter={(val) => [`${val}%`, 'Adherence']}
              />
              <Line
                type="monotone"
                dataKey="adherence"
                name="Adherence %"
                stroke="#2563eb"
                strokeWidth={3}
                dot={{ r: 4, fill: '#2563eb' }}
                activeDot={{ r: 7 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
