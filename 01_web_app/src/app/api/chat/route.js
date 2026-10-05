import { NextResponse } from 'next/server';

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
    try { data = await upstream.json(); } catch { /* non-JSON  body */ }

    // Real status is passed through; a backend failure is never returned as  HTTP 200
    if (!upstream.ok || !data) {
      return NextResponse.json({ error: 'backend_error' }, { status: upstream.ok ? 502 : upstream.status });
    }
    if (data.answer === undefined && data.reply !== undefined) data.answer = data.reply;
    if (data.request_id && !data.message_id) data.message_id = data.request_id;
    
    return NextResponse.json(data);
  } catch (err) {
    console.error('Chat proxy error:', err);
    return NextResponse.json({ error: 'backend_unavailable' }, { status: 503 });
  } finally {
    clearTimeout(timer);
  }
}