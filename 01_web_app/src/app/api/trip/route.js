import { NextResponse } from 'next/server';

export const maxDuration = 60;

const backendApiUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000';
const routePath = process.env.BACKEND_ROUTE_PATH || '/route';

const posOf = (v) => (Number.isFinite(v?.lat) && Number.isFinite(v?.lng) ? { lat: v.lat, lng: v.lng } : null);
const clean = (v) => (typeof v === 'string' ? v.trim().slice(0, 200) : '');

export async function POST(req) {
  let body;
  try { body = await req.json(); } catch { return NextResponse.json({ error: 'invalid_json' }, { status: 400 }); }

  const origin = clean(body?.origin), destination = clean(body?.destination);
  if (!origin || !destination) return NextResponse.json({ error: 'invalid_request' }, { status: 400 });
  const locale = body?.locale === 'th' ? 'th' : 'en';

  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 55000);
  try {
    const upstream = await fetch(`${backendApiUrl}${routePath}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: clean(body?.conversation_id) || null,
        origin_coords: posOf(body?.origin_coords), destination_coords: posOf(body?.destination_coords),
        origin, destination, mode: clean(body?.mode) || 'train', language: locale,
        datetime: clean(body?.datetime) || null,
        preferences: typeof body?.preferences === 'object' && body.preferences ? body.preferences : {},
      }),
      signal: ctl.signal,
    });
    let data = null;
    try { data = await upstream.json(); } catch { /* non-JSON */ }

    if (!upstream.ok || !data) {
      // A 404 from the backend normally means "endpoint not implemented yet", not "place not found".
      const notFound = upstream.status === 404 && data?.error === 'location_not_found';
      const status = notFound ? 404 : upstream.ok || upstream.status === 404 ? 502 : upstream.status;
      return NextResponse.json({ error: notFound ? 'location_not_found' : 'backend_error' }, { status });
    }
    return NextResponse.json(data);
  } catch (err) {
    console.error('Trip proxy error:', err);
    return NextResponse.json({ error: 'backend_unavailable' }, { status: 503 });
  } finally {
    clearTimeout(timer);
  }
}

