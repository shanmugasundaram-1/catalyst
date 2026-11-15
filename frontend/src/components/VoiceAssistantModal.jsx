import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import {
  Mic,
  MicOff,
  Volume2,
  X,
  Send,
  Sparkles,
  CheckCircle,
  AlertTriangle,
  Clock,
  ShieldAlert,
  Loader2,
  VolumeX
} from 'lucide-react';

export default function VoiceAssistantModal({ isOpen, onClose }) {
  const { t, i18n } = useTranslation();
  const { user, triggerRefresh } = useAuth();

  // Voice States: 'idle' | 'listening' | 'processing' | 'speaking'
  const [voiceState, setVoiceState] = useState('idle');
  const [transcript, setTranscript] = useState('');
  const [textInput, setTextInput] = useState('');
  const [response, setResponse] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [voiceAvailable, setVoiceAvailable] = useState(true);

  const recognitionRef = useRef(null);

  // Map i18n language to speech recognition / synthesis BCP-47 tag
  const getSpeechLang = (lng) => {
    switch (lng) {
      case 'hi':
        return 'hi-IN';
      case 'ta':
        return 'ta-IN';
      default:
        return 'en-IN';
    }
  };

  const currentSpeechLang = getSpeechLang(i18n.language);

  // Setup Web Speech API Recognition
  useEffect(() => {
    if (!isOpen) {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (e) {}
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      setVoiceState('idle');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = currentSpeechLang;

      recognition.onstart = () => {
        setVoiceState('listening');
        setErrorMsg('');
      };

      recognition.onresult = (event) => {
        const text = event.results[0][0].transcript;
        setTranscript(text);
        setVoiceState('processing');
        handleSendQuery(text, false);
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        setVoiceState('idle');
        if (event.error === 'not-allowed') {
          setErrorMsg('Microphone permission denied. You can type or tap the quick samples below.');
        }
      };

      recognition.onend = () => {
        if (voiceState === 'listening') {
          setVoiceState('idle');
        }
      };

      recognitionRef.current = recognition;
    } else {
      console.warn('SpeechRecognition API not supported on this device/browser.');
    }

    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (e) {}
      }
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [isOpen, currentSpeechLang]);

  // Voice synthesis speaker
  const speakReply = (text, langCode) => {
    if (!('speechSynthesis' in window)) {
      setVoiceAvailable(false);
      setVoiceState('idle');
      return;
    }

    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      const targetTag = getSpeechLang(langCode);
      utterance.lang = targetTag;
      utterance.rate = 0.9; // Elder-friendly pace

      const voices = window.speechSynthesis.getVoices();
      const matchingVoice = voices.find(
        (v) => v.lang.toLowerCase().startsWith(langCode) || v.lang.toLowerCase().includes(targetTag.toLowerCase())
      );

      if (matchingVoice) {
        utterance.voice = matchingVoice;
        setVoiceAvailable(true);
      } else {
        if (langCode === 'hi' || langCode === 'ta') {
          setVoiceAvailable(false);
        }
      }

      utterance.onstart = () => {
        setVoiceState('speaking');
      };
      utterance.onend = () => {
        setVoiceState('idle');
      };
      utterance.onerror = () => {
        setVoiceState('idle');
      };

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('Speech synthesis error:', e);
      setVoiceState('idle');
    }
  };

  const startListening = () => {
    setTranscript('');
    setErrorMsg('');
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.lang = currentSpeechLang;
        recognitionRef.current.start();
      } catch (e) {
        console.warn('Speech recognition start failed:', e);
        setVoiceState('idle');
      }
    } else {
      setErrorMsg('Speech recognition is not supported in this browser. Please use the text input below.');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }
    setVoiceState('idle');
  };

  const handleSendQuery = async (queryText, confirmed_sos = false) => {
    const q = queryText || textInput;
    if (!q || !q.trim()) return;

    setVoiceState('processing');
    setErrorMsg('');
    try {
      const res = await api.processVoiceIntent(q.trim(), i18n.language, confirmed_sos);
      setResponse(res);
      setTextInput('');
      triggerRefresh();
      speakReply(res.reply_text, res.spoken_language || i18n.language);
    } catch (err) {
      console.error('Voice intent failed:', err);
      setErrorMsg(err.message || 'Failed to process voice request. Please try again.');
      setVoiceState('idle');
    }
  };

  const handleConfirmSOS = () => {
    handleSendQuery(transcript || 'Yes send SOS', true);
  };

  const handleCancelSOS = () => {
    setResponse(null);
    setVoiceState('idle');
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  };

  // Preset example phrases for easy testing
  const examplePhrases = {
    hi: [
      'मैंने बीपी की दवा ले ली',
      'अगली दवा कब है?',
      'कल डॉक्टर का अपॉइंटमेंट है क्या?',
      'मुझे आपातकालीन मदद चाहिए'
    ],
    ta: [
      'BP maathirai saapten',
      'Next maathirai eppo?',
      'Naalaiku doctor appointment irukka?',
      'அவசர உதவி தேவை'
    ],
    en: [
      'I took my BP tablet',
      'When is my next dose?',
      'Do I have an appointment tomorrow?',
      'Emergency SOS'
    ]
  };

  const currentExamples = examplePhrases[i18n.language] || examplePhrases.en;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border-4 border-emerald-500 max-h-[92vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b pb-4 mb-5">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold">
              <Sparkles className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-slate-900 leading-tight">
                {t('voice_assistant')}
              </h2>
              <p className="text-sm font-semibold text-emerald-700">
                {i18n.language === 'hi'
                  ? 'हिन्दी आवाज़ सहायक (Web Speech + Gemini)'
                  : i18n.language === 'ta'
                  ? 'தமிழ் & Tanglish குரல் உதவியாளர்'
                  : 'Trilingual Voice Assistant (Gemini Flash)'}
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              if (window.speechSynthesis) window.speechSynthesis.cancel();
              onClose();
            }}
            className="p-2 text-slate-400 hover:text-slate-700 rounded-full hover:bg-slate-100 transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Big Elder-Friendly Microphone Interaction Area with 4 States */}
        <div className="text-center py-6 bg-slate-50 rounded-3xl border-2 border-slate-200 mb-5 relative overflow-hidden">
          {/* Active status pill */}
          <div className="mb-4">
            {voiceState === 'listening' && (
              <span className="inline-flex items-center gap-2 px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-black uppercase tracking-wider animate-pulse">
                <span className="w-2.5 h-2.5 bg-red-600 rounded-full animate-ping" />
                {t('voice_listening')}
              </span>
            )}
            {voiceState === 'processing' && (
              <span className="inline-flex items-center gap-2 px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-black uppercase tracking-wider">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                {t('voice_processing')}
              </span>
            )}
            {voiceState === 'speaking' && (
              <span className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-black uppercase tracking-wider animate-pulse">
                <Volume2 className="w-3.5 h-3.5" />
                {t('voice_speaking')}
              </span>
            )}
            {voiceState === 'idle' && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-200 text-slate-700 rounded-full text-xs font-bold">
                {t('voice_tap_to_speak')}
              </span>
            )}
          </div>

          {/* Large Floating Interactive Mic Button */}
          <button
            onClick={voiceState === 'listening' ? stopListening : startListening}
            className={`w-28 h-28 rounded-full flex items-center justify-center mx-auto shadow-2xl transition-all duration-300 transform active:scale-95 cursor-pointer ${
              voiceState === 'listening'
                ? 'bg-red-600 text-white ring-12 ring-red-200 animate-bounce'
                : voiceState === 'processing'
                ? 'bg-amber-500 text-white ring-8 ring-amber-100 animate-pulse'
                : voiceState === 'speaking'
                ? 'bg-emerald-600 text-white ring-10 ring-emerald-200 animate-pulse'
                : 'bg-emerald-600 hover:bg-emerald-700 text-white ring-8 ring-emerald-100 hover:scale-105'
            }`}
            title="Tap to speak"
          >
            {voiceState === 'listening' ? (
              <MicOff className="w-14 h-14" />
            ) : voiceState === 'processing' ? (
              <Loader2 className="w-14 h-14 animate-spin" />
            ) : voiceState === 'speaking' ? (
              <Volume2 className="w-14 h-14 animate-pulse" />
            ) : (
              <Mic className="w-14 h-14" />
            )}
          </button>

          <p className="mt-4 font-bold text-lg text-slate-900">
            {voiceState === 'listening'
              ? t('voice_listening')
              : voiceState === 'speaking'
              ? t('voice_speaking')
              : voiceState === 'processing'
              ? t('voice_processing')
              : t('voice_speak_now')}
          </p>

          {transcript && (
            <div className="mt-4 mx-4 p-3 bg-white rounded-2xl border border-slate-300 text-slate-900 font-bold text-base shadow-xs">
              "{transcript}"
            </div>
          )}
        </div>

        {/* SOS Confirmation Banner (if required) */}
        {response && response.requires_confirmation && (
          <div className="mb-5 p-5 bg-red-50 border-2 border-red-500 rounded-2xl text-center space-y-3 animate-pulse">
            <div className="flex items-center justify-center gap-2 text-red-700 font-black text-lg">
              <ShieldAlert className="w-6 h-6" />
              <span>Emergency SOS Confirmation</span>
            </div>
            <p className="text-slate-900 font-bold text-base">
              {response.reply_text}
            </p>
            <div className="flex gap-2 justify-center pt-2">
              <button
                onClick={handleConfirmSOS}
                className="px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white font-black text-sm rounded-xl shadow-md transition"
              >
                {t('voice_confirm_sos_btn')}
              </button>
              <button
                onClick={handleCancelSOS}
                className="px-4 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-800 font-bold text-sm rounded-xl transition"
              >
                {t('voice_cancel_btn')}
              </button>
            </div>
          </div>
        )}

        {/* Response Box */}
        {response && !response.requires_confirmation && (
          <div className="mb-5 p-5 bg-gradient-to-br from-emerald-50 to-teal-50 border-2 border-emerald-300 rounded-2xl shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-black uppercase tracking-wider text-emerald-800 bg-emerald-200/70 px-2.5 py-1 rounded-md">
                Intent: {response.intent}
              </span>
              <button
                onClick={() => speakReply(response.reply_text, response.spoken_language || i18n.language)}
                title="Speak again"
                className="p-1.5 bg-white text-emerald-700 hover:bg-emerald-100 rounded-lg border border-emerald-300 transition"
              >
                <Volume2 className="w-4 h-4" />
              </button>
            </div>

            {/* Elder-friendly large response text */}
            <p className="text-xl sm:text-2xl font-black text-slate-900 leading-snug my-2">
              {response.reply_text}
            </p>

            {response.action_performed && (
              <div className="mt-3 flex items-center gap-2 text-xs font-bold text-emerald-800 bg-white/90 p-2.5 rounded-xl border border-emerald-200">
                <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>Action: {response.action_performed}</span>
              </div>
            )}

            {!voiceAvailable && (
              <p className="text-xs text-slate-500 font-medium mt-2 italic flex items-center gap-1">
                <VolumeX className="w-3.5 h-3.5" />
                No local voice detected for this language — displayed as text above.
              </p>
            )}
          </div>
        )}

        {/* Quick Sample Query Chips */}
        <div className="mb-5">
          <p className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2">
            {i18n.language === 'hi'
              ? 'त्वरित परीक्षण के लिए क्लिक करें:'
              : i18n.language === 'ta'
              ? 'மாதிரி கட்டளைகள் (தமிழ் / Tanglish):'
              : 'Try asking:'}
          </p>
          <div className="flex flex-wrap gap-2">
            {currentExamples.map((phrase, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setTranscript(phrase);
                  handleSendQuery(phrase, false);
                }}
                className="text-xs sm:text-sm font-semibold bg-emerald-50 hover:bg-emerald-100 text-emerald-800 px-3 py-1.5 rounded-xl border border-emerald-200 transition text-left cursor-pointer"
              >
                💬 {phrase}
              </button>
            ))}
          </div>
        </div>

        {/* Text Input Fallback */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendQuery()}
            placeholder={
              i18n.language === 'hi'
                ? 'या यहाँ टाइप करें (उदा. मैंने दवा ले ली)...'
                : i18n.language === 'ta'
                ? 'அல்லது தட்டச்சு செய்யவும்...'
                : 'Or type a query here...'
            }
            className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
          <button
            onClick={() => handleSendQuery()}
            disabled={voiceState === 'processing' || !textInput.trim()}
            className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white p-2.5 rounded-xl transition cursor-pointer"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>

        {/* Error message */}
        {errorMsg && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-xl text-sm font-semibold">
            {errorMsg}
          </div>
        )}
      </div>
    </div>
  );
}
