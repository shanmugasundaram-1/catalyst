import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  ShieldCheck,
  CheckCircle,
  XCircle,
  Clock,
  User,
  AlertCircle,
  Lock,
  Unlock,
  Sparkles
} from 'lucide-react';

export default function ApprovalsPage() {
  const { t } = useTranslation();
  const { user, refreshTrigger, triggerRefresh } = useAuth();
  const [pendingChanges, setPendingChanges] = useState([]);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewingId, setReviewingId] = useState(null);
  const [statusMsg, setStatusMsg] = useState('');

  const isElder = user?.role === 'ELDER';

  useEffect(() => {
    fetchData();
  }, [refreshTrigger, user]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await api.listPendingChanges('PENDING');
      setPendingChanges(data || []);
      const prof = await api.getCurrentProfile();
      setProfile(prof);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (changeId, action) => {
    if (!isElder) {
      alert('Only the Elder has the authority to approve or decline healthcare proposals.');
      return;
    }
    setReviewingId(changeId);
    try {
      await api.reviewPendingChange(changeId, action);
      setStatusMsg(`Proposal ${action === 'APPROVE' ? 'Approved & Applied' : 'Declined'}.`);
      fetchData();
      triggerRefresh();
      setTimeout(() => setStatusMsg(''), 4000);
    } catch (err) {
      alert(err.message || 'Action failed');
    } finally {
      setReviewingId(null);
    }
  };

  const handleToggleAutoApprove = async () => {
    if (!isElder) return;
    try {
      const updated = await api.updateProfileSettings({
        auto_approve_caretaker: !profile.auto_approve_caretaker
      });
      setProfile(updated);
      setStatusMsg(
        updated.auto_approve_caretaker
          ? 'Auto-approve ENABLED for Caretaker modifications.'
          : 'Strict Elder Approval ENABLED: All Caretaker changes require your manual confirmation.'
      );
      setTimeout(() => setStatusMsg(''), 4000);
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="space-y-6 sm:space-y-8 animate-fade-in">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 shadow-xs border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-700 mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span>Elder-Centered Care Authority</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            {t('nav_approvals')} ({pendingChanges.length})
          </h2>
          <p className="text-slate-500 font-medium text-sm mt-0.5">
            You hold full control over your health regimen. Changes proposed by caretakers or family require your review.
          </p>
        </div>

        {/* Elder Auto-Approve Toggle */}
        {isElder && profile && (
          <div className="bg-slate-50 p-4 rounded-2xl border-2 border-slate-200 flex items-center justify-between gap-4 self-start md:self-auto min-w-[280px]">
            <div className="flex items-center gap-2.5">
              {profile.auto_approve_caretaker ? (
                <Unlock className="w-5 h-5 text-amber-600" />
              ) : (
                <Lock className="w-5 h-5 text-emerald-700" />
              )}
              <div>
                <span className="text-xs font-bold text-slate-800 block">Auto-Approve Caretaker</span>
                <span className="text-xs text-slate-500">
                  {profile.auto_approve_caretaker ? 'Enabled (Direct changes)' : 'Disabled (Strict review)'}
                </span>
              </div>
            </div>
            <button
              onClick={handleToggleAutoApprove}
              className={`px-3.5 py-1.5 rounded-xl font-bold text-xs transition ${
                profile.auto_approve_caretaker
                  ? 'bg-amber-100 text-amber-900 hover:bg-amber-200'
                  : 'bg-emerald-600 text-white hover:bg-emerald-700'
              }`}
            >
              {profile.auto_approve_caretaker ? 'Turn Off' : 'Turn On'}
            </button>
          </div>
        )}
      </div>

      {statusMsg && (
        <div className="p-4 bg-emerald-50 border-2 border-emerald-300 text-emerald-900 rounded-2xl font-bold text-sm flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      {!isElder && (
        <div className="p-4 bg-blue-50 border-2 border-blue-200 rounded-2xl text-blue-900 text-sm font-semibold flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0" />
          <span>
            You are logged in as <span className="font-bold uppercase">{user?.role}</span>. Any changes you propose appear here until approved by Elder <span className="font-bold">{user?.profile_name}</span>.
          </span>
        </div>
      )}

      {/* Pending Items List */}
      {pendingChanges.length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center border-2 border-slate-200 space-y-3">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle className="w-8 h-8" />
          </div>
          <h3 className="text-xl font-black text-slate-900">No Pending Approvals!</h3>
          <p className="text-slate-500 text-sm font-medium max-w-md mx-auto">
            All proposed medications, schedule changes, and doctor appointments have been reviewed.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {pendingChanges.map((item) => {
            const isSubmitting = reviewingId === item.id;
            const payload = item.payload || {};
            const timeAgo = new Date(item.proposed_at).toLocaleString([], {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            });

            return (
              <div
                key={item.id}
                className="bg-white rounded-3xl p-6 sm:p-7 border-3 border-amber-300 shadow-md space-y-5"
              >
                {/* Proposal Meta Header */}
                <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100 text-sm">
                  <div className="flex items-center gap-2 text-slate-700">
                    <User className="w-4 h-4 text-blue-600" />
                    <span className="font-bold text-slate-900">{item.proposed_by_name}</span>
                    <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 font-extrabold text-xs">
                      {item.proposed_by_role}
                    </span>
                    <span className="text-slate-400 font-medium">proposed a change</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 font-semibold">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <span>{timeAgo}</span>
                  </div>
                </div>

                {/* Proposal Content */}
                <div className="bg-amber-50/50 rounded-2xl p-5 border border-amber-200 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <span className="text-xs font-black uppercase tracking-wider text-amber-800 block">
                        {item.entity_type} {item.action_type} REQUEST
                      </span>
                      <h4 className="text-2xl font-black text-slate-950 mt-0.5">
                        {payload.name || payload.doctor_name || 'Item'} {payload.dosage ? `(${payload.dosage})` : ''}
                      </h4>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs sm:text-sm font-semibold text-slate-700">
                    {payload.food_timing && (
                      <p>
                        <span className="font-bold text-slate-500">Food Instruction:</span>{' '}
                        {payload.food_timing.replace('_', ' ')}
                      </p>
                    )}
                    {payload.schedule_times && (
                      <p>
                        <span className="font-bold text-slate-500">Times:</span>{' '}
                        {payload.schedule_times.join(', ')}
                      </p>
                    )}
                    {payload.location && (
                      <p>
                        <span className="font-bold text-slate-500">Clinic Location:</span> {payload.location}
                      </p>
                    )}
                    {payload.instructions && (
                      <p className="col-span-full italic text-slate-600">
                        Reason/Note: "{payload.instructions}"
                      </p>
                    )}
                  </div>
                </div>

                {/* Actions for Elder */}
                {isElder ? (
                  <div className="flex items-center justify-end gap-3 pt-2">
                    <button
                      onClick={() => handleReview(item.id, 'REJECT')}
                      disabled={isSubmitting}
                      className="px-5 py-3 rounded-2xl bg-slate-100 hover:bg-red-50 text-slate-700 hover:text-red-700 font-bold text-sm transition flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                    >
                      <XCircle className="w-5 h-5" />
                      <span>{t('reject_btn')}</span>
                    </button>
                    <button
                      onClick={() => handleReview(item.id, 'APPROVE')}
                      disabled={isSubmitting}
                      className="px-7 py-3 rounded-2xl bg-emerald-600 hover:bg-emerald-700 active:scale-95 text-white font-black text-base shadow-md transition flex items-center gap-2 disabled:opacity-50 cursor-pointer"
                    >
                      <CheckCircle className="w-5 h-5" />
                      <span>{isSubmitting ? 'Approving...' : t('approve_btn')}</span>
                    </button>
                  </div>
                ) : (
                  <div className="text-right text-xs text-slate-500 italic font-semibold">
                    Awaiting Elder review and confirmation.
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
