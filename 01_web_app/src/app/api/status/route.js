import { NextResponse } from 'next/server';

const backendApiUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000';
const statusPath = process.env.BACKEND_STATUS_PATH; // e.g. /status — optional; ask 02 for a health endpoint

export async function GET() {
  if (process.env.MOCK_BACKEND === 'true') {
    return NextResponse.json({ mock: true, live_sources: ['weather', 'flight', 'traffic'], degraded: true });
  }
  if (!statusPath) return NextResponse.json({ error: 'status_endpoint_not_configured' }, { status: 404 });
  try {
    const res = await fetch(`${backendApiUrl}${statusPath}`, { cache: 'no-store', signal: AbortSignal.timeout(8000) });
    const data = await res.json().catch(() => null);
    if (!res.ok || !data) return NextResponse.json({ error: 'backend_error' }, { status: 502 });
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: 'backend_unavailable' }, { status: 503 });
  }
}
