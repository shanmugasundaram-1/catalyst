import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  Calendar,
  Clock,
  MapPin,
  CheckCircle,
  Plus,
  Trash2,
  BellRing,
  UserCheck
} from 'lucide-react';

export default function AppointmentsPage() {
  const { t } = useTranslation();
  const { user, refreshTrigger } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  // Form state
  const [doctorName, setDoctorName] = useState('');
  const [specialty, setSpecialty] = useState('Cardiologist');
  const [appointmentTime, setAppointmentTime] = useState('');
  const [location, setLocation] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    fetchAppointments();
  }, [refreshTrigger, user]);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const data = await api.listAppointments();
      setAppointments(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddAppointment = async (e) => {
    e.preventDefault();
    if (!doctorName || !appointmentTime) return;
    try {
      const res = await api.createAppointment({
        doctor_name: doctorName.trim(),
        specialty: specialty.trim(),
        appointment_time: new Date(appointmentTime).toISOString(),
        location: location.trim() || 'City Clinic',
        notes: notes.trim()
      });

      setStatusMsg(
        res.status === 'APPROVED'
          ? `Appointment with Dr. ${doctorName} scheduled!`
          : `Appointment proposal submitted for Elder review.`
      );

      setDoctorName('');
      setNotes('');
      setShowAddModal(false);
      fetchAppointments();
      setTimeout(() => setStatusMsg(''), 4000);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleToggleComplete = async (id, currentStatus) => {
    try {
      await api.toggleAppointmentComplete(id, !currentStatus);
      fetchAppointments();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDelete = async (id, docName) => {
    if (!window.confirm(`Cancel appointment with Dr. ${docName}?`)) return;
    try {
      await api.deleteAppointment(id);
      fetchAppointments();
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 shadow-xs border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {t('nav_appointments')} ({appointments.length})
          </h2>
          <p className="text-slate-500 font-medium text-sm mt-0.5">
            Automated 24-hour and 2-hour reminders sent via email before every visit.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-black rounded-2xl text-sm shadow-md flex items-center gap-1.5 transition self-start sm:self-auto cursor-pointer"
        >
          <Plus className="w-5 h-5" />
          <span>Schedule Visit</span>
        </button>
      </div>

      {statusMsg && (
        <div className="p-4 bg-emerald-50 border-2 border-emerald-300 text-emerald-900 rounded-2xl font-bold text-sm flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* Appointments List */}
      {appointments.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center border-2 border-slate-200 space-y-3">
          <Calendar className="w-12 h-12 text-slate-400 mx-auto" />
          <h3 className="text-xl font-bold text-slate-800">No Appointments Scheduled</h3>
          <p className="text-slate-500 text-sm max-w-sm mx-auto">
            Add upcoming doctor checkups, lab visits, or specialist consultations.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {appointments.map((appt) => {
            const dateObj = new Date(appt.appointment_time);
            const dateStr = dateObj.toLocaleDateString([], {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
              year: 'numeric'
            });
            const timeStr = dateObj.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            });

            return (
              <div
                key={appt.id}
                className={`p-6 rounded-3xl border-2 transition flex flex-col sm:flex-row sm:items-center justify-between gap-5 ${
                  appt.is_completed
                    ? 'bg-slate-50 border-slate-200 opacity-70'
                    : 'bg-white border-slate-200 hover:border-emerald-400 shadow-xs'
                }`}
              >
                <div className="flex items-start gap-4">
                  <div className="w-14 h-14 rounded-2xl bg-teal-50 border border-teal-200 text-teal-800 flex flex-col items-center justify-center font-bold flex-shrink-0">
                    <span className="text-xs uppercase leading-none">{dateObj.toLocaleString('default', { month: 'short' })}</span>
                    <span className="text-xl font-black">{dateObj.getDate()}</span>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-xl font-black text-slate-900">
                        Dr. {appt.doctor_name}
                      </h4>
                      <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border">
                        {appt.specialty}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-xs font-semibold text-slate-600">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{timeStr}</span>
                      </span>
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" />
                        <span>{appt.location}</span>
                      </span>
                      <span className="flex items-center gap-1 text-emerald-700">
                        <BellRing className="w-3.5 h-3.5" />
                        <span>24h & 2h reminders enabled</span>
                      </span>
                    </div>

                    {appt.notes && (
                      <p className="text-xs text-slate-500 pt-1 italic font-medium">
                        "{appt.notes}"
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-auto">
                  <button
                    onClick={() => handleToggleComplete(appt.id, appt.is_completed)}
                    className={`px-4 py-2 rounded-xl font-bold text-xs transition flex items-center gap-1.5 ${
                      appt.is_completed
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-100 hover:bg-emerald-50 text-slate-700 hover:text-emerald-700'
                    }`}
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>{appt.is_completed ? 'Completed' : 'Mark Done'}</span>
                  </button>
                  <button
                    onClick={() => handleDelete(appt.id, appt.doctor_name)}
                    className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Appointment Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-slate-200 animate-scale-up space-y-5">
            <h3 className="text-2xl font-black text-slate-900">Schedule Doctor Visit</h3>
            <form onSubmit={handleAddAppointment} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Doctor Name *</label>
                <input
                  type="text"
                  required
                  value={doctorName}
                  onChange={(e) => setDoctorName(e.target.value)}
                  placeholder="e.g. K. Ramanathan"
                  className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Specialty</label>
                  <input
                    type="text"
                    value={specialty}
                    onChange={(e) => setSpecialty(e.target.value)}
                    placeholder="Cardiologist, Diabetologist"
                    className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Date & Time *</label>
                  <input
                    type="datetime-local"
                    required
                    value={appointmentTime}
                    onChange={(e) => setAppointmentTime(e.target.value)}
                    className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Location / Clinic</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Apollo Heart Centre, Room 204"
                  className="w-full p-3 rounded-xl border border-slate-300 font-semibold text-slate-900 text-sm focus:border-emerald-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Notes / Purpose</label>
                <input
                  type="text"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Blood pressure check, ECG review"
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
                  className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-black rounded-xl text-sm transition shadow-md"
                >
                  Confirm Visit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
