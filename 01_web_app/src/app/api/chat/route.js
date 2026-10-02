import { NextResponse } from 'next/server';
import { buildMockTrip } from '@/lib/mockTrip';

export const maxDuration = 60;

// Keeps the env name already used by the project. Server-only (no NEXT_PUBLIC_).
const backendApiUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000';
// Current backend exposes /ask; switch to /api/chat with BACKEND_CHAT_PATH when module 02 is ready.
const chatPath = process.env.BACKEND_CHAT_PATH || '/ask';

export async function POST(req) {
  let body;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'invalid_json' }, { status: 400 });
  }

  const { conversation_id, message, locale, messages, trip_context } = body ?? {};
  if (typeof message !== 'string' || !message.trim() || message.length > 2000 || typeof conversation_id !== 'string') {
    return NextResponse.json({ error: 'invalid_request' }, { status: 400 });
  }

  // Dev-only: set MOCK_BACKEND=true in .env.local to test the UI without module 02. Off by default.
  if (process.env.MOCK_BACKEND === 'true') {
    const th = locale === 'th';
    const q = message.toLowerCase();
    const level = /earthquake|แผ่นดินไหว|ฮาโกดาเตะ|hakodate/.test(q) ? 'AVOID_TRAVEL' : /train|delay|รถไฟ|ล่าช้า/.test(q) ? 'WARNING' : 'SAFE';
    const text = {
      SAFE: th ? '[ข้อมูลจำลอง] สภาพอากาศปกติ เดินทางได้ตามปกติ' : '[MOCK] Conditions look normal. Travel as planned.',
      WARNING: th ? '[ข้อมูลจำลอง] ดึงสถานะรถไฟสดไม่ได้ ควรตรวจสอบก่อนเดินทาง' : '[MOCK] Live train status is unavailable. Please check before travelling.',
      AVOID_TRAVEL: th ? '[ข้อมูลจำลอง] ตรวจพบแผ่นดินไหวรุนแรง หลีกเลี่ยงการเดินทางและไปศูนย์อพยพ' : '[MOCK] Strong earthquake detected. Avoid travel and go to a shelter.',
    }[level];
    await new Promise((r) => setTimeout(r, 800));
    const base = {
      message_id: `mock-${Date.now()}`,
      answer: text,
      safety_level: level,
      status: level === 'WARNING' ? 'degraded' : 'ok',
      sources_used: ['Mock data'],
      live_sources: level === 'WARNING' ? ['weather', 'flight', 'traffic'] : ['weather', 'train', 'flight', 'traffic'],
      degraded: level === 'WARNING',
    };
    // Demo route_intent: asking about Otaru opens the map beside the chat with origin/destination pre-filled
    if (/otaru|โอตารุ/i.test(message)) base.route_intent = { origin: th ? 'ซัปโปโร' : 'Sapporo Station', destination: th ? 'โอตารุ' : 'Otaru Station', mode: 'train' };
    // Demo: a route-related question with a filled trip form returns new routes, like the real backend should
    let tripPart = {};
    const tc = trip_context;
    if (tc?.origin && tc?.destination && /route|เส้นทาง|avoid|เลี่ยง|snow|หิมะ|detour/i.test(message)) {
      const r = await buildMockTrip(String(tc.origin), String(tc.destination), th ? 'th' : 'en', { origin: tc.origin_coords, destination: tc.destination_coords }, ['train', 'bus', 'car'].includes(tc.mode) ? tc.mode : 'car');
      if (r.status === 200) tripPart = { ...r.body, trip: { origin: tc.origin, destination: tc.destination, datetime: tc.datetime, preferences: { ...(tc.preferences || {}), avoid_mountain: true } } };
    }
    return NextResponse.json({ ...base, ...tripPart });
  }

  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 55000);
  try {
    const upstream = await fetch(`${backendApiUrl}${chatPath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id,
        message,
        language: locale === 'th' ? 'th' : 'en',
        messages: Array.isArray(messages) ? messages.slice(-21) : [{ role: 'user', content: message }],
        trip_context: trip_context && typeof trip_context === 'object' ? trip_context : null,
        enabled_agents: { weather: true, disaster: true, train: true },
      }),
      signal: ctl.signal,
    });

    let data = null;
    try { data = await upstream.json(); } catch { /* non-JSON body */ }

    // Real status is passed through; a backend failure is never returned as HTTP 200
    if (!upstream.ok || !data) {
      return NextResponse.json({ error: 'backend_error' }, { status: upstream.ok ? 502 : upstream.status });
    }
    if (data.answer === undefined && data.reply !== undefined) data.answer = data.reply;
    return NextResponse.json(data);
  } catch (err) {
    console.error('Chat proxy error:', err);
    return NextResponse.json({ error: 'backend_unavailable' }, { status: 503 });
  } finally {
    clearTimeout(timer);
  }
}
