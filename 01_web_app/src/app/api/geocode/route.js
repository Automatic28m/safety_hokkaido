import { NextResponse } from 'next/server';

// Server-side proxy for Mapbox geocoding: avoids browser "Failed to fetch" problems
// (ad blockers, VPN/firewall, token URL restrictions) and keeps the request in one place.
const TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || process.env.MAPBOX_TOKEN;

export async function GET(req) {
  if (!TOKEN) return NextResponse.json({ error: 'mapbox_token_missing' }, { status: 503 });

  const sp = req.nextUrl.searchParams;
  const q = (sp.get('q') || '').trim().slice(0, 200);
  const hasCoords = sp.get('lat') !== null && sp.get('lng') !== null;
  const lat = Number(sp.get('lat')), lng = Number(sp.get('lng'));

  let path;
  if (q.length >= 2) {
    // Forward search, biased toward Hokkaido
    path = `${encodeURIComponent(q)}.json?country=jp&autocomplete=true&limit=5&proximity=141.35,43.06`;
  } else if (hasCoords && Number.isFinite(lat) && Number.isFinite(lng)) {
    // Reverse: nearest named place to a dragged pin / GPS position
    path = `${lng},${lat}.json?types=poi,address,place`;
  } else {
    return NextResponse.json({ error: 'invalid_request' }, { status: 400 });
  }

  try {
    const res = await fetch(`https://api.mapbox.com/geocoding/v5/mapbox.places/${path}&access_token=${TOKEN}`, { signal: AbortSignal.timeout(8000) });
    if (!res.ok) return NextResponse.json({ error: 'geocoder_error' }, { status: 502 });
    const data = await res.json();
    const places = (data.features || []).map((f) => ({
      id: f.id, text: f.text, place_name: f.place_name, lat: f.center[1], lng: f.center[0],
    }));
    return NextResponse.json({ places });
  } catch (err) {
    console.warn('Geocode proxy error:', err.message);
    return NextResponse.json({ error: 'geocoder_unavailable' }, { status: 503 });
  }
}
