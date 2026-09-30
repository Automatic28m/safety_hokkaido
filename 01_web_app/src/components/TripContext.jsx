'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

// Shared by the trip form (page) and the chat (modal in the layout).
// This file only stores and displays what the backend returns. It never computes or picks routes.
const Ctx = createContext(null);

export const useTrip = () => {
  const c = useContext(Ctx);
  if (!c) throw new Error('useTrip must be used inside <TripProvider>');
  return c;
};

const pos = (o) => (Number.isFinite(o?.lat) && Number.isFinite(o?.lng) ? { lat: o.lat, lng: o.lng } : null);
const pad = (n) => String(n).padStart(2, '0');
const EMPTY_FORM = { origin: '', destination: '', date: '', time: '', priority: 'safest', avoidMountain: false, originPos: null, destPos: null };

export function TripProvider({ children }) {
  const [conversationId, setConversationId] = useState(null); // same id for form + chat -> same memory in 02
  const [form, setForm] = useState(EMPTY_FORM);
  const [result, setResult] = useState(null);

  // Client-only defaults (avoids hydration mismatch)
  useEffect(() => {
    setConversationId(crypto.randomUUID());
    const d = new Date();
    setForm((f) => ({ ...f, date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`, time: `${pad(d.getHours())}:${pad(d.getMinutes())}` }));
  }, []);

  // data = backend response. Returns true if it contained drawable routes.
  // syncForm: also copy the trip the backend understood from the chat (origin/destination/time/preferences) into the form.
  const applyBackendTrip = useCallback((data, { syncForm = false } = {}) => {
    const routes = (Array.isArray(data?.routes) ? data.routes : []).filter((r) => r?.id && r.geometry?.length > 1);
    const tr = data?.trip;
    setForm((f) => {
      let n = f;
      if (syncForm && tr && typeof tr === 'object') {
        const oText = typeof tr.origin === 'string' ? tr.origin : f.origin;
        const dText = typeof tr.destination === 'string' ? tr.destination : f.destination;
        n = {
          ...n, origin: oText, destination: dText,
          // If the backend changed a place, use the position it understood; otherwise keep the user's pin
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
    setResult({ ...data, routes });
    return true;
  }, []);

  const value = useMemo(() => ({ conversationId, form, setForm, result, setResult, applyBackendTrip }), [conversationId, form, result, applyBackendTrip]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
