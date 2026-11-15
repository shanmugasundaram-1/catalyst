import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  Pill,
  Plus,
  AlertTriangle,
  Clock,
  Utensils,
  Trash2,
  CheckCircle,
  PackageCheck,
  Search
} from 'lucide-react';

export default function MedicationsPage({ onOpenAI }) {
  const { t } = useTranslation();
  const { user, refreshTrigger } = useAuth();
  const [meds, setMeds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [search, setSearch] = useState('');
  const [statusMsg, setStatusMsg] = useState('');

  // Form state
  const [name, setName] = useState('');
  const [dosage, setDosage] = useState('');
  const [frequency, setFrequency] = useState('DAILY');
  const [scheduleTimes, setScheduleTimes] = useState('09:00');
  const [foodTiming, setFoodTiming] = useState('AFTER_FOOD');
  const [stockCount, setStockCount] = useState(30);
  const [lowStockThreshold, setLowStockThreshold] = useState(5);
  const [instructions, setInstructions] = useState('');

  useEffect(() => {
    fetchMeds();
  }, [refreshTrigger, user]);

  const fetchMeds = async () => {
    setLoading(true);
    try {
      const data = await api.listMedications();
      setMeds(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMed = async (e) => {
    e.preventDefault();
    if (!name || !dosage) return;
    try {
      const times = scheduleTimes.split(',').map((s) => s.trim());
      const res = await api.createMedication({
        name: name.trim(),
        dosage: dosage.trim(),
        frequency,
        schedule_times: times,
        food_timing: foodTiming,
        start_date: new Date().toISOString().split('T')[0],
        stock_count: parseInt(stockCount, 10) || 30,
        low_stock_threshold: parseInt(lowStockThreshold, 10) || 5,
        instructions: instructions.trim()
      });

      setStatusMsg(
        res.status === 'APPROVED'
          ? `Medication '${name}' added to your active schedule!`
          : `Proposal submitted! Since you are ${user?.role}, Elder ${user?.profile_name} will review and approve this change.`
      );

      // Reset form
      setName('');
      setDosage('');
      setInstructions('');
      setShowAddModal(false);
      fetchMeds();
      setTimeout(() => setStatusMsg(''), 4500);
    } catch (err) {
      alert(err.message || 'Failed to add medication');
    }
  };

  const handleDelete = async (id, medName) => {
    if (!window.confirm(`Are you sure you want to remove '${medName}'?`)) return;
    try {
      const res = await api.deleteMedication(id);
      setStatusMsg(res.message || 'Medication updated');
      fetchMeds();
      setTimeout(() => setStatusMsg(''), 3500);
    } catch (err) {
      alert(err.message);
    }
  };

  const filteredMeds = meds.filter((m) =>
    m.name.toLowerCase().includes(search.toLowerCase()) ||
    m.dosage.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 shadow-xs border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {t('nav_medications')} ({meds.length})
          </h2>
          <p className="text-slate-500 font-medium text-sm mt-0.5">
            Dosages, scheduled times, food timings, and automatic stock tracking.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onOpenAI}
            className="px-4 py-2.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border-2 border-emerald-300 font-bold rounded-2xl text-sm transition"
          >
            ✨ AI Scanner
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-black rounded-2xl text-sm shadow-md flex items-center gap-1.5 transition"
          >
            <Plus className="w-5 h-5" />
            <span>Add Medicine</span>
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className="p-4 bg-emerald-50 border-2 border-emerald-300 text-emerald-900 rounded-2xl font-bold text-sm flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* Search Input */}
      <div className="relative">
        <Search className="w-5 h-5 text-slate-400 absolute left-4 top-3.5" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by medicine name or dosage..."
          className="w-full pl-12 pr-4 py-3 bg-white rounded-2xl border-2 border-slate-200 focus:border-emerald-500 focus:outline-none font-medium text-slate-900 text-sm shadow-xs"
        />
      </div>

      {/* Medication Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
        {filteredMeds.map((med) => {
          const isLowStock = med.stock_count <= med.low_stock_threshold;
          return (
            <div
              key={med.id}
              className="bg-white rounded-3xl p-6 border-2 border-slate-200 hover:border-emerald-400 shadow-xs hover:shadow-md transition space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0">
                      <Pill className="w-7 h-7" />
                    </div>
                    <div>
                      <h3 className="text-xl sm:text-2xl font-black text-slate-950">
                        {med.name}
                      </h3>
                      <p className="text-base font-bold text-emerald-700">{med.dosage}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDelete(med.id, med.name)}
                    className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition"
                    title="Remove Medicine"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>

                {/* Badges for food & timings */}
                <div className="flex flex-wrap items-center gap-2 text-xs font-bold">
                  <span className="px-3 py-1 rounded-xl bg-blue-50 text-blue-900 border border-blue-200 flex items-center gap-1.5">
                    <Utensils className="w-3.5 h-3.5" />
                    <span>{med.food_timing.replace('_', ' ')}</span>
                  </span>
                  <span className="px-3 py-1 rounded-xl bg-slate-100 text-slate-800 border border-slate-200 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Times: {med.schedule_times.join(', ')}</span>
                  </span>
                </div>

                {med.instructions && (
                  <p className="text-xs text-slate-600 italic bg-slate-50 p-3 rounded-xl border border-slate-200">
                    "{med.instructions}"
                  </p>
                )}
              </div>

              {/* Bottom Stock Tracker */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <PackageCheck className="w-5 h-5 text-slate-500" />
                  <span className="text-sm font-bold text-slate-700">
                    Stock:{' '}
                    <span className={`font-black ${isLowStock ? 'text-red-600 text-base' : 'text-slate-900'}`}>
                      {med.stock_count} pills
                    </span>
                  </span>
                </div>

                {isLowStock && (
                  <span className="px-3 py-1 rounded-full bg-red-100 text-red-800 border border-red-300 text-xs font-black flex items-center gap-1 animate-pulse">
                    <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                    <span>Low Stock (Refill)</span>
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Medication Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-slate-200 animate-scale-up space-y-5">
            <h3 className="text-2xl font-black text-slate-900">Add New Medication</h3>
            <p className="text-xs text-slate-500 font-medium">
              {user?.role === 'ELDER'
                ? 'As Elder, this medicine will be added directly to your regimen.'
                : 'As Caretaker or Family, this will be submitted for Elder confirmation.'}
            </p>

            <form onSubmit={handleAddMed} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Medicine Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Metformin Hydrochloride"
                  className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Dosage *</label>
                  <input
                    type="text"
                    required
                    value={dosage}
                    onChange={(e) => setDosage(e.target.value)}
                    placeholder="e.g. 500 mg, 1 tablet"
                    className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Daily Times</label>
                  <input
                    type="text"
                    value={scheduleTimes}
                    onChange={(e) => setScheduleTimes(e.target.value)}
                    placeholder="09:00, 21:00"
                    className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Food Timing</label>
                  <select
                    value={foodTiming}
                    onChange={(e) => setFoodTiming(e.target.value)}
                    className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none bg-white"
                  >
                    <option value="AFTER_FOOD">After Food</option>
                    <option value="BEFORE_FOOD">Before Food</option>
                    <option value="WITH_FOOD">With Food</option>
                    <option value="ANYTIME">Anytime</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Stock Count</label>
                  <input
                    type="number"
                    value={stockCount}
                    onChange={(e) => setStockCount(e.target.value)}
                    className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Special Instructions</label>
                <input
                  type="text"
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  placeholder="e.g. Take with lukewarm water; avoid citrus"
                  className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div className="flex gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 rounded-xl font-bold text-slate-700 text-sm transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-black rounded-xl text-sm transition shadow-md"
                >
                  Save Medication
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
