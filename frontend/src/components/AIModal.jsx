import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import {
  Sparkles,
  Camera,
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  X,
  Plus,
  Trash2,
  Clock,
  Utensils
} from 'lucide-react';

export default function AIModal({ isOpen, onClose, onMedsAdded, isElder }) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('scan'); // 'scan' or 'nl'
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [nlText, setNlText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [extractedMeds, setExtractedMeds] = useState([]);
  const [diagnosisInfo, setDiagnosisInfo] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  if (!isOpen) return null;

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
      setError('');
    }
  };

  const handleScanPrescription = async () => {
    if (!file) {
      setError('Please choose or snap a photo of the prescription.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await api.scanPrescription(file);
      setExtractedMeds(res.medications || []);
      setDiagnosisInfo(res.diagnosis_or_notes || '');
    } catch (err) {
      setError(err.message || 'Failed to scan prescription image');
    } finally {
      setLoading(false);
    }
  };

  const handleParseNL = async () => {
    if (!nlText.trim()) {
      setError('Please type or speak medication instructions.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await api.parseNaturalLanguage(nlText);
      setExtractedMeds([res]);
    } catch (err) {
      setError(err.message || 'Failed to parse natural language instructions');
    } finally {
      setLoading(false);
    }
  };

  const handleMedChange = (index, field, value) => {
    const updated = [...extractedMeds];
    updated[index][field] = value;
    setExtractedMeds(updated);
  };

  const handleRemoveMed = (index) => {
    setExtractedMeds(extractedMeds.filter((_, i) => i !== index));
  };

  const handleConfirmAndAddAll = async () => {
    if (extractedMeds.length === 0) return;
    setLoading(true);
    setError('');
    try {
      let addedCount = 0;
      for (const med of extractedMeds) {
        await api.createMedication({
          name: med.name,
          dosage: med.dosage || '1 dose',
          frequency: med.frequency || 'DAILY',
          schedule_times: med.schedule_times || ['09:00'],
          food_timing: med.food_timing || 'AFTER_FOOD',
          start_date: new Date().toISOString().split('T')[0],
          stock_count: 30,
          low_stock_threshold: 5,
          instructions: med.instructions || ''
        });
        addedCount++;
      }
      setSuccessMsg(
        isElder
          ? `Success! Added ${addedCount} medications directly to your active schedule.`
          : `Submitted ${addedCount} medications for Elder approval.`
      );
      if (onMedsAdded) onMedsAdded();
      setTimeout(() => {
        onClose();
      }, 1800);
    } catch (err) {
      setError(err.message || 'Failed to add medications');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[90vh] flex flex-col overflow-hidden shadow-2xl border border-slate-200 animate-scale-up">
        {/* Header */}
        <div className="bg-gradient-to-r from-emerald-600 to-teal-700 text-white p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-amber-300" />
            </div>
            <div>
              <h2 className="text-2xl font-black tracking-tight">Gemini AI Medication Assistant</h2>
              <p className="text-emerald-100 text-xs sm:text-sm font-medium">
                Prescription Vision Scanner & Natural Language Parser
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-white hover:bg-white/20 rounded-full transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex border-b border-slate-200 bg-slate-50 px-6 pt-3">
          <button
            onClick={() => {
              setActiveTab('scan');
              setExtractedMeds([]);
            }}
            className={`pb-3 px-4 font-bold text-sm sm:text-base border-b-2 transition flex items-center gap-2 ${
              activeTab === 'scan'
                ? 'border-emerald-600 text-emerald-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Camera className="w-5 h-5" />
            <span>Prescription Photo Scanner</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('nl');
              setExtractedMeds([]);
            }}
            className={`pb-3 px-4 font-bold text-sm sm:text-base border-b-2 transition flex items-center gap-2 ${
              activeTab === 'nl'
                ? 'border-emerald-600 text-emerald-800'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <FileText className="w-5 h-5" />
            <span>Natural Language Entry</span>
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {error && (
            <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-2xl text-sm font-bold flex items-center gap-2">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-4 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded-2xl text-sm font-bold flex items-center gap-2">
              <CheckCircle className="w-5 h-5 flex-shrink-0 text-emerald-600" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* TAB 1: Prescription Scanner */}
          {activeTab === 'scan' && extractedMeds.length === 0 && (
            <div className="space-y-4">
              <div className="border-2 border-dashed border-slate-300 rounded-3xl p-8 text-center hover:border-emerald-500 transition bg-slate-50">
                <input
                  type="file"
                  id="prescription-file"
                  accept="image/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label
                  htmlFor="prescription-file"
                  className="cursor-pointer flex flex-col items-center justify-center gap-3"
                >
                  <div className="w-16 h-16 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                    <Upload className="w-8 h-8" />
                  </div>
                  <div>
                    <span className="text-lg font-bold text-slate-800">
                      Click to upload prescription photo
                    </span>
                    <p className="text-xs text-slate-500 mt-1">
                      Supports JPG, PNG, mobile camera snapshots (Gemini Vision extracts medicines, dosage & timing)
                    </p>
                  </div>
                </label>
              </div>

              {previewUrl && (
                <div className="bg-slate-100 p-4 rounded-2xl flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <img
                      src={previewUrl}
                      alt="Prescription preview"
                      className="w-16 h-16 object-cover rounded-xl border border-slate-300 shadow-sm"
                    />
                    <div>
                      <p className="text-sm font-bold text-slate-800">{file?.name}</p>
                      <p className="text-xs text-slate-500">Ready for Gemini Vision extraction</p>
                    </div>
                  </div>
                  <button
                    onClick={handleScanPrescription}
                    disabled={loading}
                    className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-bold text-sm rounded-xl transition flex items-center gap-2 disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4" />
                    <span>{loading ? 'Scanning with Gemini...' : 'Extract Medicines'}</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Natural Language Entry */}
          {activeTab === 'nl' && extractedMeds.length === 0 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-2">
                  Describe the medicine instructions in plain language:
                </label>
                <textarea
                  rows={3}
                  value={nlText}
                  onChange={(e) => setNlText(e.target.value)}
                  placeholder="e.g., Metformin 500mg morning and night after food for 30 days"
                  className="w-full p-4 rounded-2xl border-2 border-slate-200 focus:border-emerald-500 focus:outline-none text-slate-900 font-medium text-base shadow-inner"
                />
              </div>

              {/* Quick sample chips */}
              <div className="flex flex-wrap gap-2 text-xs">
                <span className="font-bold text-slate-500 self-center">Try:</span>
                {[
                  'Telmisartan 40mg once morning before food',
                  'मेटफॉर्मिन 500mg सुबह और रात खाने के बाद 30 दिन के लिए',
                  'Atorvastatin 10mg every night after dinner',
                  'வைட்டமின் D3 வாரம் ஒரு முறை ஞாயிறு காலை'
                ].map((sample, i) => (
                  <button
                    key={i}
                    onClick={() => setNlText(sample)}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-lg font-medium transition text-left"
                  >
                    "{sample}"
                  </button>
                ))}
              </div>

              <button
                onClick={handleParseNL}
                disabled={loading || !nlText.trim()}
                className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-bold text-base rounded-2xl transition flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Sparkles className="w-5 h-5" />
                <span>{loading ? 'AI Parsing...' : 'Parse into Schedule'}</span>
              </button>
            </div>
          )}

          {/* Extracted Preview List (Editable before final confirmation) */}
          {extractedMeds.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-black text-slate-900">
                    Review Extracted Medicines ({extractedMeds.length})
                  </h3>
                  <p className="text-xs text-slate-500">
                    Verify and make adjustments if needed before adding to the care schedule.
                  </p>
                </div>
                <button
                  onClick={() => setExtractedMeds([])}
                  className="text-xs text-slate-500 hover:text-slate-800 underline font-semibold"
                >
                  Scan Another
                </button>
              </div>

              {diagnosisInfo && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs font-semibold text-blue-900">
                  Doctor Notes: {diagnosisInfo}
                </div>
              )}

              <div className="space-y-3">
                {extractedMeds.map((med, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl border-2 border-emerald-200 bg-emerald-50/40 space-y-3"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <input
                        type="text"
                        value={med.name}
                        onChange={(e) => handleMedChange(idx, 'name', e.target.value)}
                        placeholder="Medicine Name"
                        className="font-black text-slate-900 text-lg bg-transparent border-b border-dashed border-slate-300 focus:outline-none focus:border-emerald-500 flex-1"
                      />
                      <input
                        type="text"
                        value={med.dosage}
                        onChange={(e) => handleMedChange(idx, 'dosage', e.target.value)}
                        placeholder="Dosage"
                        className="font-bold text-emerald-800 text-base bg-white px-2.5 py-1 rounded-lg border border-slate-200 focus:outline-none w-32"
                      />
                      <button
                        onClick={() => handleRemoveMed(idx)}
                        className="p-1.5 text-slate-400 hover:text-red-600 transition"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div>
                        <label className="text-xs font-bold text-slate-500 block mb-1">
                          Food Timing
                        </label>
                        <select
                          value={med.food_timing}
                          onChange={(e) => handleMedChange(idx, 'food_timing', e.target.value)}
                          className="w-full bg-white p-2 rounded-xl border border-slate-300 text-slate-800 font-semibold text-xs"
                        >
                          <option value="AFTER_FOOD">After Food</option>
                          <option value="BEFORE_FOOD">Before Food</option>
                          <option value="WITH_FOOD">With Food</option>
                          <option value="ANYTIME">Anytime</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-xs font-bold text-slate-500 block mb-1">
                          Daily Times
                        </label>
                        <input
                          type="text"
                          value={med.schedule_times?.join(', ') || '09:00'}
                          onChange={(e) =>
                            handleMedChange(
                              idx,
                              'schedule_times',
                              e.target.value.split(',').map((s) => s.trim())
                            )
                          }
                          placeholder="09:00, 21:00"
                          className="w-full bg-white p-2 rounded-xl border border-slate-300 text-slate-800 font-semibold text-xs"
                        />
                      </div>
                    </div>

                    {med.instructions && (
                      <p className="text-xs text-slate-600 italic">
                        Tip: {med.instructions}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              {/* Confirm and Add Button */}
              <button
                onClick={handleConfirmAndAddAll}
                disabled={loading}
                className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-black text-lg rounded-2xl shadow-lg transition flex items-center justify-center gap-3 disabled:opacity-50"
              >
                <CheckCircle className="w-6 h-6" />
                <span>
                  {loading
                    ? 'Saving...'
                    : isElder
                    ? 'Confirm & Add to My Schedule'
                    : 'Submit for Elder Confirmation'}
                </span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
