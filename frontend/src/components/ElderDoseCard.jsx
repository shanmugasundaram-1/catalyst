import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { CheckCircle2, Clock, Utensils, Pill, Award, AlertCircle } from 'lucide-react';

export default function ElderDoseCard({ nextDose, onTakeDose, isElderOrCaretaker }) {
  const { t } = useTranslation();
  const [submitting, setSubmitting] = useState(false);

  if (!nextDose) {
    return (
      <div className="bg-gradient-to-r from-emerald-500 to-teal-600 rounded-3xl p-6 sm:p-8 text-white shadow-xl text-center">
        <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-4 backdrop-blur-sm">
          <Award className="w-10 h-10 text-white" />
        </div>
        <h2 className="text-2xl sm:text-3xl font-black mb-2">
          {t('status_taken')} - All Caught Up!
        </h2>
        <p className="text-emerald-100 text-lg font-medium max-w-lg mx-auto">
          Wonderful job! You have taken all your scheduled medications for today. Rest well and stay hydrated.
        </p>
      </div>
    );
  }

  const timeFormatted = new Date(nextDose.scheduled_time).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });

  const getFoodBadge = (timing) => {
    switch (timing) {
      case 'BEFORE_FOOD':
        return { label: t('food_before'), bg: 'bg-amber-100 text-amber-900 border-amber-300' };
      case 'AFTER_FOOD':
        return { label: t('food_after'), bg: 'bg-blue-100 text-blue-900 border-blue-300' };
      case 'WITH_FOOD':
        return { label: t('food_with'), bg: 'bg-purple-100 text-purple-900 border-purple-300' };
      default:
        return { label: t('food_anytime'), bg: 'bg-slate-100 text-slate-800 border-slate-300' };
    }
  };

  const foodInfo = getFoodBadge(nextDose.food_timing);

  const handleTake = async () => {
    setSubmitting(true);
    try {
      await onTakeDose(nextDose.id);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white border-4 border-emerald-500 rounded-3xl p-6 sm:p-9 shadow-xl relative overflow-hidden">
      {/* Top Banner Ribbon */}
      <div className="flex items-center justify-between gap-4 mb-4 pb-4 border-b-2 border-slate-100">
        <div className="flex items-center gap-2 text-emerald-800">
          <div className="w-4 h-4 rounded-full bg-emerald-500 animate-ping" />
          <span className="text-sm sm:text-base font-black uppercase tracking-wider">
            {t('today_next_dose')}
          </span>
        </div>
        <div className="flex items-center gap-2 bg-slate-100 px-3.5 py-1.5 rounded-full border border-slate-200">
          <Clock className="w-5 h-5 text-slate-700" />
          <span className="text-lg sm:text-xl font-black text-slate-900">
            {timeFormatted}
          </span>
        </div>
      </div>

      {/* Main Medicine Name & Dosage */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center shadow-inner">
              <Pill className="w-7 h-7" />
            </div>
            <div>
              <h3 className="text-3xl sm:text-4xl font-black text-slate-950 tracking-tight leading-tight">
                {nextDose.medication_name}
              </h3>
              <p className="text-xl sm:text-2xl font-bold text-emerald-700">
                {nextDose.dosage}
              </p>
            </div>
          </div>

          {/* Food Instruction Badge */}
          <div className="pt-2 flex flex-wrap items-center gap-2">
            <span className={`inline-flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-base font-bold border-2 ${foodInfo.bg}`}>
              <Utensils className="w-5 h-5" />
              {foodInfo.label}
            </span>
            {nextDose.notes && (
              <span className="inline-flex items-center gap-1.5 bg-slate-100 px-3 py-1.5 rounded-xl text-sm font-semibold text-slate-700 border border-slate-200">
                Note: {nextDose.notes}
              </span>
            )}
          </div>
        </div>

        {/* Big Giant "I Took It" Button */}
        {isElderOrCaretaker ? (
          <button
            onClick={handleTake}
            disabled={submitting}
            className="w-full md:w-auto min-w-[280px] bg-emerald-600 hover:bg-emerald-700 active:scale-95 disabled:opacity-50 text-white font-black text-xl sm:text-2xl px-8 py-5 rounded-2xl shadow-lg shadow-emerald-600/30 flex items-center justify-center gap-3 transition transform cursor-pointer"
          >
            <CheckCircle2 className="w-8 h-8 flex-shrink-0" />
            <span>{submitting ? 'Updating...' : t('i_took_it')}</span>
          </button>
        ) : (
          <div className="p-4 bg-purple-50 border-2 border-purple-200 rounded-2xl text-purple-900 text-sm font-semibold max-w-xs text-center">
            👨‍👩‍👧 Family Observer Mode: You can view schedule & alerts. Elder or Caretaker confirms doses.
          </div>
        )}
      </div>
    </div>
  );
}
