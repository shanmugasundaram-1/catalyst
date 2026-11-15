import React, { createContext, useContext, useState, useEffect } from 'react';
import { api, setToken, getToken } from '../api/client';
import i18n from '../i18n';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('ayucare_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);
  const [largeFont, setLargeFont] = useState(() => {
    return localStorage.getItem('ayucare_large_font') === 'true';
  });
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const triggerRefresh = () => setRefreshTrigger((prev) => prev + 1);

  const toggleLargeFont = () => {
    setLargeFont((prev) => {
      const next = !prev;
      localStorage.setItem('ayucare_large_font', String(next));
      return next;
    });
  };

  useEffect(() => {
    async function initUser() {
      const token = getToken();
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.getMe();
        const profile = await api.getCurrentProfile();
        const memberLang = me.language || profile.language || 'en';
        const updated = {
          ...me,
          profile_name: profile.full_name,
          language: memberLang,
          auto_approve_caretaker: profile.auto_approve_caretaker
        };
        setUser(updated);
        localStorage.setItem('ayucare_user', JSON.stringify(updated));
        if (memberLang) {
          i18n.changeLanguage(memberLang);
          localStorage.setItem('ayucare_lang', memberLang);
        }
      } catch (err) {
        console.error('Session verify failed:', err);
        // If demo profile is accessible, auto-login with default elder for seamless hackathon UX
      } finally {
        setLoading(false);
      }
    }
    initUser();
  }, []);

  const loginWithPasscode = async ({ profile_id, passcode, name, email, language }) => {
    const data = await api.joinProfile({ profile_id, passcode, name, email, language });
    setToken(data.access_token);
    const userLang = data.language || language || 'en';
    const userInfo = {
      profile_id: data.profile_id,
      profile_name: data.profile_name,
      role: data.role,
      name: data.name,
      email: data.email,
      language: userLang,
      auto_approve_caretaker: data.auto_approve_caretaker
    };
    setUser(userInfo);
    localStorage.setItem('ayucare_user', JSON.stringify(userInfo));
    i18n.changeLanguage(userLang);
    localStorage.setItem('ayucare_lang', userLang);
    triggerRefresh();
    return userInfo;
  };

  const changeLanguage = async (newLang) => {
    i18n.changeLanguage(newLang);
    localStorage.setItem('ayucare_lang', newLang);
    if (user) {
      const updated = { ...user, language: newLang };
      setUser(updated);
      localStorage.setItem('ayucare_user', JSON.stringify(updated));
      try {
        await api.updateMemberLanguage(newLang);
      } catch (err) {
        console.warn('Failed to persist language to backend:', err);
      }
    }
    triggerRefresh();
  };

  // Quick switch role utility (for instant 1-click hackathon judging & demo!)
  const quickSwitchRole = async (targetRole) => {
    const passcodes = {
      ELDER: { code: '1111', name: 'Sundaram Raman (Elder)', email: 'sundaram@ayucare.demo', lang: 'ta' },
      CARETAKER: { code: '2222', name: 'Priya (Nurse Caretaker)', email: 'priya.care@ayucare.demo', lang: 'en' },
      FAMILY: { code: '3333', name: 'Karthik Sundaram (Son)', email: 'karthik.family@ayucare.demo', lang: 'hi' }
    };
    const cred = passcodes[targetRole];
    if (!cred) return;
    return await loginWithPasscode({
      profile_id: user?.profile_id || 'DEMO-ELDER',
      passcode: cred.code,
      name: cred.name,
      email: cred.email,
      language: cred.lang
    });
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('ayucare_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        largeFont,
        toggleLargeFont,
        loginWithPasscode,
        quickSwitchRole,
        changeLanguage,
        logout,
        refreshTrigger,
        triggerRefresh
      }}
    >
      <div className={largeFont ? 'text-lg select-text font-medium' : 'text-base select-text'}>
        {children}
      </div>
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
