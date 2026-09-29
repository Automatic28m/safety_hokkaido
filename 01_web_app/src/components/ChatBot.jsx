'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { useTranslations, useLocale } from 'next-intl';

const LEVEL_STYLE = {
  SAFE: 'bg-green-700',
  WARNING: 'bg-amber-500',
  AVOID_TRAVEL: 'bg-red-600',
};
const LEVEL_ICON = { SAFE: '🟢', WARNING: '🟡', AVOID_TRAVEL: '🔴' };
const SERVICES = ['weather', 'train', 'flight', 'traffic'];
const DOT_STYLE = { ok: 'bg-green-500', degraded: 'bg-amber-400', down: 'bg-red-500' };

const now = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

export default function ChatBot({ isOpen, onClose }) {
  const t = useTranslations('Chat');
  const locale = useLocale();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [serviceStatus, setServiceStatus] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  // Created client-side only (avoids hydration mismatch). Memory on the backend is keyed by this id.
  useEffect(() => {
    setConversationId(crypto.randomUUID());
  }, []);

  // Greeting follows the current locale
  useEffect(() => {
    setMessages((prev) =>
      prev.length <= 1 ? [{ role: 'ai', content: t('greeting'), timestamp: now() }] : prev
    );
  }, [locale, t]);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : 'unset';
    if (isOpen) scrollToBottom();
    return () => { document.body.style.overflow = 'unset'; };
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) scrollToBottom();
  }, [messages, isLoading, isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen, onClose]);

  const pushAi = (msg) =>
    setMessages((prev) => [...prev, { role: 'ai', timestamp: now(), ...msg }]);

  const send = async (raw) => {
    const text = raw.trim();
    if (!text || isLoading || !conversationId) return;

    setMessages((prev) => [...prev, { role: 'user', content: text, timestamp: now() }]);
    setInput('');
    setIsLoading(true);

    // Recent history is still sent because the current backend (/ask) is stateless; conversation_id serves the new contract
    const history = messages
      .filter((m) => !m.isError)
      .slice(-20)
      .map((m) => ({ role: m.role, content: m.content }));

    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 58000);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: text,
          locale,
          messages: [...history, { role: 'user', content: text }],
        }),
        signal: ctl.signal,
      });

      if (!res.ok) {
        // Never hide backend failures behind a fake answer
        pushAi({ content: res.status === 503 ? t('errorUnavailable') : t('errorGeneric'), isError: true });
        return;
      }

      const data = await res.json();
      if (data.service_status) setServiceStatus(data.service_status);
      pushAi({
        id: data.message_id || `${Date.now()}`,
        content: data.answer ?? data.reply ?? t('errorGeneric'),
        safetyLevel: LEVEL_STYLE[data.safety_level] ? data.safety_level : null,
        degraded: data.status === 'degraded',
        sources: Array.isArray(data.sources_used) ? data.sources_used : [],
      });
    } catch (error) {
      console.error('Chat Error:', error);
      pushAi({
        content: error.name === 'AbortError' ? t('errorTimeout') : t('errorUnavailable'),
        isError: true,
      });
    } finally {
      clearTimeout(timer);
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    send(input);
  };

  const sendFeedback = async (index, rating) => {
    const msg = messages[index];
    if (!msg?.id || msg.rating) return;
    setMessages((prev) => prev.map((m, i) => (i === index ? { ...m, rating } : m)));
    try {
      const res = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId, message_id: msg.id, rating }),
      });
      if (!res.ok) throw new Error(String(res.status));
    } catch {
      setMessages((prev) => prev.map((m, i) => (i === index ? { ...m, rating: null } : m)));
    }
  };

  const sourceLabel = (s) =>
    typeof s === 'string' ? s : `${s.name || s.id}${s.page ? ` (p.${s.page})` : ''}`;

  if (!isOpen) return null;

  return (
    <>
      {/* Blurred Backdrop */}
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[90]" onClick={onClose} aria-hidden="true" />

      <div className="fixed top-6 bottom-8 left-[5%] right-[5%] sm:top-1/2 sm:left-1/2 sm:bottom-auto sm:right-auto sm:-translate-x-1/2 sm:-translate-y-1/2 sm:w-[90vw] sm:max-w-5xl sm:h-[90vh] bg-white rounded-3xl shadow-2xl z-[100] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-b from-[#0c59cc] to-[#1bb38e] pt-6 pb-5 px-6 flex items-center justify-between relative shrink-0 shadow-md z-10">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-[72px] h-[72px] relative bg-white rounded-full overflow-hidden shadow-sm border-[3px] border-white">
                <Image src="/illustrations/AI Profile.png" alt="Tamago" fill sizes="72px" className="object-cover" />
              </div>
              <div className="absolute top-0 right-1 w-4 h-4 bg-[#34d399] border-2 border-[#0f60c2] rounded-full shadow-sm"></div>
            </div>
            <div className="flex flex-col">
              <h2 className="text-white font-bold text-2xl tracking-wide leading-tight">Tamago</h2>
              <p className="text-white text-sm opacity-90 mt-0.5">
                {t('ready')} <br />
                <span className="text-xs opacity-75">Using AI model: gpt-oss-120b</span>
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-white p-2 hover:bg-white/20 rounded-full transition-colors self-start mt-2" aria-label="Close chat">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
          </button>
        </div>

        {/* Data source status lights (from backend service_status) */}
        <div className="shrink-0 flex flex-wrap gap-x-4 gap-y-1 px-6 py-2 bg-white border-b border-gray-200 text-xs text-gray-600" aria-label={t('servicesTitle')}>
          {SERVICES.map((k) => {
            const st = serviceStatus?.[k];
            return (
              <span key={k} className="flex items-center gap-1.5">
                <i className={`inline-block w-2.5 h-2.5 rounded-full ${DOT_STYLE[st] || 'bg-gray-300'}`} />
                {t(`services.${k}`)}
              </span>
            );
          })}
        </div>

        {/* Chat Area */}
        <div className="flex-1 p-4 overflow-y-auto overscroll-none bg-gray-50 flex flex-col gap-6">
          {messages.map((msg, index) => (
            <div key={index} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'user' ? (
                <div className="flex flex-col items-end gap-1.5 w-[90%]">
                  <div className="px-6 py-4 rounded-3xl bg-[#0c4ca3] text-white w-full shadow-sm">
                    <div className="text-sm whitespace-pre-wrap">{msg.content}</div>
                  </div>
                  <span className="text-xs text-gray-500 font-medium tracking-wide mr-2">{msg.timestamp}</span>
                </div>
              ) : (
                <div className="flex flex-col items-start gap-2 w-[90%]">
                  {msg.safetyLevel && (
                    <div className={`w-full rounded-2xl px-5 py-3 text-white shadow-sm ${LEVEL_STYLE[msg.safetyLevel]}`} role="alert">
                      <div className="font-bold text-lg">{LEVEL_ICON[msg.safetyLevel]} {t(`levels.${msg.safetyLevel}`)}</div>
                      {msg.safetyLevel === 'AVOID_TRAVEL' && (
                        <Link href={`/${locale}/emergency-contact`} onClick={onClose} className="block text-sm mt-1 underline opacity-95">
                          {t('emergencyNumbers')}
                        </Link>
                      )}
                    </div>
                  )}
                  <div className={`px-6 py-4 rounded-3xl w-full shadow-sm ${msg.isError ? 'bg-red-50 text-red-800 border border-red-200' : 'bg-gray-100 text-gray-800'}`}>
                    <div className="prose prose-sm prose-slate max-w-none prose-p:leading-relaxed prose-li:my-0.5">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                    {msg.degraded && (
                      <p className="mt-3 text-xs font-semibold text-amber-700">⚠️ {t('degraded')}</p>
                    )}
                    {msg.sources?.length > 0 && (
                      <p className="mt-2 text-xs text-gray-500">{t('sources')}: {msg.sources.map(sourceLabel).join(', ')}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2.5 ml-2">
                    <div className="w-10 h-10 relative rounded-full overflow-hidden shrink-0 shadow-sm border border-gray-200">
                      <Image src="/illustrations/AI Profile.png" alt="Tamago" fill sizes="40px" className="object-cover" />
                    </div>
                    {msg.timestamp && (
                      <span className="text-xs text-gray-500 font-medium tracking-wide mt-1">{msg.timestamp}</span>
                    )}
                    {msg.id && (
                      <div className="flex gap-1 mt-1">
                        {[['up', '👍', 'helpful'], ['down', '👎', 'notHelpful']].map(([r, icon, label]) => (
                          <button
                            key={r}
                            onClick={() => sendFeedback(index, r)}
                            disabled={!!msg.rating}
                            aria-label={t(label)}
                            className={`text-sm px-2 py-0.5 rounded-full border transition-colors ${msg.rating === r ? 'bg-[#0c4ca3] border-[#0c4ca3]' : 'border-gray-300 hover:bg-gray-200'} disabled:opacity-60`}
                          >
                            {icon}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex w-fit justify-start">
              <div className="flex flex-col items-start gap-2 w-[90%]">
                <div className="px-6 py-4 rounded-3xl bg-gray-100 shadow-sm w-full" aria-live="polite" aria-label={t('thinking')}>
                  <div className="flex gap-1.5 items-center h-full pt-1 pb-0.5">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  </div>
                </div>
                <div className="w-10 h-10 relative rounded-full overflow-hidden shrink-0 shadow-sm border border-gray-200 ml-2">
                  <Image src="/illustrations/AI Profile.png" alt="Tamago" fill sizes="40px" className="object-cover" />
                </div>
              </div>
            </div>
          )}

          {messages.length <= 1 && !isLoading && (
            <div className="flex flex-wrap gap-2 pl-1">
              {t.raw('suggestions').map((q) => (
                <button key={q} type="button" onClick={() => send(q)} className="px-4 py-2 rounded-full border-2 border-[#0c4ca3] text-[#0c4ca3] bg-white text-sm font-semibold text-left hover:bg-[#0c4ca3] hover:text-white transition-colors">
                  {q}
                </button>
              ))}
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-gray-50 shrink-0 pb-8 sm:pb-4">
          <form onSubmit={handleSubmit} className="bg-white border-2 border-gray-200 rounded-full flex items-center px-3 py-2 gap-3 shadow-sm">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
              placeholder={t('placeholder')}
              maxLength={2000}
              enterKeyHint="send"
              autoComplete="off"
              className="flex-1 bg-transparent outline-none min-w-0 text-lg placeholder:text-gray-500 text-gray-700"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="w-12 h-12 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 hover:bg-orange-500 transition-colors disabled:opacity-50"
              aria-label="Send message"
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m12 19 0-14" /><path d="m5 12 7-7 7 7" /></svg>
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
