// In production, set VITE_API_BASE_URL to your backend URL (e.g. https://ayucare.onrender.com/api)
// In development, Vite proxy handles /api → localhost:8000
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export function getToken() {
  return localStorage.getItem('ayucare_token');
}

export function setToken(token) {
  if (token) {
    localStorage.setItem('ayucare_token', token);
  } else {
    localStorage.removeItem('ayucare_token');
  }
}

async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    ...(options.headers || {})
  };

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    // If unauthorized, clear token if expired
    // Let caller handle or redirect to login
  }

  if (!response.ok) {
    let errMessage = `Error ${response.status}: ${response.statusText}`;
    try {
      const errData = await response.json();
      if (errData && errData.detail) {
        errMessage = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
      }
    } catch (e) {
      // keep fallback
    }
    throw new Error(errMessage);
  }

  return response.json();
}

export const api = {
  // Auth
  joinProfile: (data) => request('/auth/join', { method: 'POST', body: JSON.stringify(data) }),
  registerProfile: (data) => request('/auth/register-profile', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request('/auth/me'),

  // Profile & Settings
  getCurrentProfile: () => request('/profiles/current'),
  updateProfileSettings: (data) => request('/profiles/current', { method: 'PATCH', body: JSON.stringify(data) }),
  updateMemberLanguage: (language) => request('/profiles/member-language', { method: 'PATCH', body: JSON.stringify({ language }) }),

  // Medications
  listMedications: (activeOnly = false) => request(`/medications?active_only=${activeOnly}`),
  createMedication: (data) => request('/medications', { method: 'POST', body: JSON.stringify(data) }),
  updateMedication: (id, data) => request(`/medications/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteMedication: (id) => request(`/medications/${id}`, { method: 'DELETE' }),

  // Dose Tracking
  getTodayOverview: () => request('/doses/today'),
  recordDoseAction: (doseId, status, notes = '') =>
    request(`/doses/${doseId}/action`, { method: 'POST', body: JSON.stringify({ status, notes }) }),
  getDoseHistory: (days = 7) => request(`/doses/history?days=${days}`),

  // Appointments
  listAppointments: (upcomingOnly = false) => request(`/appointments?upcoming_only=${upcomingOnly}`),
  createAppointment: (data) => request('/appointments', { method: 'POST', body: JSON.stringify(data) }),
  toggleAppointmentComplete: (id, completed) =>
    request(`/appointments/${id}/status?completed=${completed}`, { method: 'PATCH' }),
  deleteAppointment: (id) => request(`/appointments/${id}`, { method: 'DELETE' }),

  // Approvals (Elder-at-the-center)
  listPendingChanges: (status = 'PENDING') => request(`/approvals?status_filter=${status}`),
  reviewPendingChange: (id, action, rejectionReason = '') =>
    request(`/approvals/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({ action, rejection_reason: rejectionReason })
    }),

  // Activity Log
  getActivityLogs: (limit = 50) => request(`/activity?limit=${limit}`),

  // AI Features
  scanPrescription: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return request('/ai/scan-prescription', { method: 'POST', body: formData });
  },
  parseNaturalLanguage: (text) =>
    request('/ai/parse-natural-language', { method: 'POST', body: JSON.stringify({ text }) }),
  checkDrugInteraction: (newMedicine, currentMedicines = []) =>
    request('/ai/check-interaction', {
      method: 'POST',
      body: JSON.stringify({ new_medicine: newMedicine, current_medicines: currentMedicines })
    }),
  getWeeklySummary: (sendEmail = false) =>
    request(`/ai/weekly-summary?send_email=${sendEmail}`, { method: 'POST' }),

  // Recent Sent Emails Inspector (Live demo)
  getRecentEmails: () => request('/ai/recent-emails'),

  // Emergency SOS
  triggerSOS: (locationNote = 'Home') =>
    request('/sos', { method: 'POST', body: JSON.stringify({ location_note: locationNote }) }),

  // Voice Assistant
  processVoiceIntent: (query, language = 'en', confirmed_sos = false) =>
    request('/voice/intent', { method: 'POST', body: JSON.stringify({ query, language, confirmed_sos }) }),

  // AI Early Warning & Care Insights
  getInsights: (limit = 20) => request(`/insights?limit=${limit}`),
  analyzeInsightsNow: () => request('/insights/analyze', { method: 'POST' }),
  markInsightSeen: (id) => request(`/insights/${id}/seen`, { method: 'POST' })
};
