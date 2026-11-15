import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Mail, X, RefreshCw, Clock, ExternalLink } from 'lucide-react';

export default function LiveEmailDrawer({ isOpen, onClose }) {
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchEmails();
    }
  }, [isOpen]);

  const fetchEmails = async () => {
    setLoading(true);
    try {
      const data = await api.getRecentEmails();
      setEmails(data || []);
      if (data && data.length > 0 && !selectedEmail) {
        setSelectedEmail(data[0]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-xs">
      <div className="bg-white w-full max-w-2xl h-full flex flex-col shadow-2xl animate-slide-left">
        {/* Drawer Header */}
        <div className="bg-slate-900 text-white p-5 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <Mail className="w-6 h-6 text-amber-400" />
            <div>
              <h2 className="text-lg font-black">Live Email & Escalation Audit</h2>
              <p className="text-xs text-slate-400">Scheduler & Escalation Engine Dispatch Log</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchEmails}
              disabled={loading}
              className="p-2 text-slate-300 hover:text-white rounded-lg hover:bg-slate-800 transition"
              title="Refresh Emails"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button onClick={onClose} className="p-2 text-slate-300 hover:text-white rounded-lg hover:bg-slate-800 transition">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body Split */}
        <div className="flex-1 flex flex-col sm:flex-row overflow-hidden">
          {/* Left Email List */}
          <div className="w-full sm:w-2/5 border-r border-slate-200 overflow-y-auto bg-slate-50 p-2 space-y-1.5">
            {emails.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500 font-semibold">
                No emails dispatched yet. Trigger an SOS or complete a dose!
              </div>
            ) : (
              emails.map((item, idx) => {
                const isSelected = selectedEmail === item;
                const time = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                return (
                  <button
                    key={idx}
                    onClick={() => setSelectedEmail(item)}
                    className={`w-full text-left p-3 rounded-xl border transition cursor-pointer ${
                      isSelected
                        ? 'bg-white border-blue-500 shadow-sm'
                        : 'bg-white/70 border-slate-200 hover:bg-white'
                    }`}
                  >
                    <div className="flex justify-between items-center text-xs text-slate-400 mb-1">
                      <span className="font-bold text-slate-500">{time}</span>
                      <span className="truncate max-w-[90px]">{item.to[0]}</span>
                    </div>
                    <p className="font-bold text-slate-900 text-xs line-clamp-1">
                      {item.subject}
                    </p>
                  </button>
                );
              })
            )}
          </div>

          {/* Right Rendered Email Preview */}
          <div className="w-full sm:w-3/5 overflow-y-auto p-4 flex flex-col">
            {selectedEmail ? (
              <div className="space-y-3 flex-1 flex flex-col">
                <div className="bg-slate-100 p-3 rounded-xl space-y-1 text-xs">
                  <div>
                    <span className="font-bold text-slate-500">To:</span>{' '}
                    <span className="font-mono text-slate-900 font-bold">{selectedEmail.to.join(', ')}</span>
                  </div>
                  <div>
                    <span className="font-bold text-slate-500">Subject:</span>{' '}
                    <span className="font-bold text-slate-900">{selectedEmail.subject}</span>
                  </div>
                  <div>
                    <span className="font-bold text-slate-500">Dispatched:</span>{' '}
                    <span className="text-slate-700">{new Date(selectedEmail.timestamp).toLocaleString()}</span>
                  </div>
                </div>

                <div className="flex-1 border rounded-xl overflow-hidden bg-white shadow-xs">
                  <iframe
                    title="Email Render"
                    srcDoc={selectedEmail.html}
                    className="w-full h-full min-h-[380px] border-none"
                  />
                </div>
              </div>
            ) : (
              <div className="m-auto text-slate-400 text-sm font-semibold">
                Select an email on the left to preview the HTML template.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
