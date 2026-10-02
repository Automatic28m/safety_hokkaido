'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { normalizeSources } from '@/lib/sourceStatus';

// Shared by the trip form (page), the chat (modal in the layout) and the status dots (navbar).
// This file only stores and displays what the backend returns. It never computes or picks routes.
const Ctx = createContext(null);

export const useTrip = () => {
  const c = useContext(Ctx);
  if (!c) throw new Error('useTrip must be used inside <TripProvider>');
  return c;
};

export const MODES = ['train', 'bus', 'car'];
const pad = (n) => String(n).padStart(2, '0');
const pos = (o) => (Number.isFinite(o?.lat) && Number.isFinite(o?.lng) ? { lat: o.lat, lng: o.lng } : null);
const EMPTY_FORM = { origin: '', destination: '', date: '', time: '', priority: 'safest', avoidMountain: false, originPos: null, destPos: null };
const OFFLINE = { live_sources: [], degraded: false };

export function TripProvider({ children }) {
  const [conversationId, setConversationId] = useState(null); // same id for form + chat -> same memory in 02
  const [form, setForm] = useState(EMPTY_FORM);
  const [results, setResults] = useState({}); // one result per transport mode, so Train / Bus / Car maps differ
  const [activeMode, setActiveMode] = useState('train');
  const [sourceStatus, setSourceStatus] = useState({});

  // Client-only defaults (avoids hydration mismatch)
  useEffect(() => {
    setConversationId(crypto.randomUUID());
    const d = new Date();
    setForm((f) => ({ ...f, date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`, time: `${pad(d.getHours())}:${pad(d.getMinutes())}` }));
  }, []);

  const updateSources = useCallback((data) => {
    const n = normalizeSources(data);
    if (n) setSourceStatus((p) => ({ ...p, ...n }));
  }, []);

  // Initial / periodic status for the navbar dots, when the backend exposes one (BACKEND_STATUS_PATH)
  useEffect(() => {
    let stopped = false;
    let timer;
    const poll = async () => {
      try {
        const res = await fetch('/api/status', { cache: 'no-store' });
        if (res.status === 404) return; // not configured: dots update from chat / route responses instead
        updateSources(res.ok ? await res.json() : OFFLINE);
      } catch {
        updateSources(OFFLINE);
      }
      if (!stopped) timer = setTimeout(poll, 60000);
    };
    poll();
    return () => { stopped = true; clearTimeout(timer); };
  }, [updateSources]);

  const resultFor = useCallback((m) => results[m] ?? null, [results]);
  const setResultFor = useCallback((m, v) => setResults((r) => ({ ...r, [m]: v })), []);

  // data = backend response. Returns true if it contained drawable routes.
  // syncForm: also copy the trip the backend understood from the chat into the form.
  const applyBackendTrip = useCallback((data, { syncForm = false, mode = 'train' } = {}) => {
    const routes = (Array.isArray(data?.routes) ? data.routes : []).filter((r) => r?.id && r.geometry?.length > 1);
    const tr = data?.trip;
    setForm((f) => {
      let n = f;
      if (syncForm && tr && typeof tr === 'object') {
        const oText = typeof tr.origin === 'string' ? tr.origin : f.origin;
        const dText = typeof tr.destination === 'string' ? tr.destination : f.destination;
        n = {
          ...n, origin: oText, destination: dText,
          originPos: oText !== f.origin ? (pos(tr.origin_coords) ?? pos(data.origin)) : f.originPos,
          destPos: dText !== f.destination ? (pos(tr.destination_coords) ?? pos(data.destination)) : f.destPos,
          ...(typeof tr.datetime === 'string' && tr.datetime.length >= 16 ? { date: tr.datetime.slice(0, 10), time: tr.datetime.slice(11, 16) } : {}),
          priority: ['safest', 'fastest'].includes(tr.preferences?.priority) ? tr.preferences.priority : f.priority,
          avoidMountain: typeof tr.preferences?.avoid_mountain === 'boolean' ? tr.preferences.avoid_mountain : f.avoidMountain,
        };
      }
      if (routes.length) n = { ...n, originPos: n.originPos ?? pos(data.origin), destPos: n.destPos ?? pos(data.destination) };
      return n;
    });
    if (!routes.length) return false;
    const m = MODES.includes(mode) ? mode : 'train';
    setResults((r) => ({ ...r, [m]: { ...data, routes } }));
    return true;
  }, []);

  const value = useMemo(
    () => ({ conversationId, form, setForm, activeMode, setActiveMode, resultFor, setResultFor, applyBackendTrip, sourceStatus, updateSources }),
    [conversationId, form, activeMode, resultFor, setResultFor, applyBackendTrip, sourceStatus, updateSources]
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
