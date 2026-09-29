// Dev-only demo (MOCK_BACKEND=true). Real road geometry from Mapbox, but the "safe" route,
// risk levels and warnings are placeholders. In production this data comes from the backend (02).
const TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;

async function mb(url) {
  const res = await fetch(url, { signal: AbortSignal.timeout(10000) });
  if (!res.ok) throw new Error(`Mapbox HTTP ${res.status}`);
  return res.json();
}
async function geocode(q) {
  const d = await mb(`https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(q)}.json?country=jp&limit=1&proximity=141.35,43.06&access_token=${TOKEN}`);
  const f = d.features?.[0];
  return f ? { lng: f.center[0], lat: f.center[1], label: f.place_name } : null;
}
async function directions(coords, alternatives) {
  const path = coords.map((c) => c.join(',')).join(';');
  const d = await mb(`https://api.mapbox.com/directions/v5/mapbox/driving/${path}?geometries=geojson&overview=full&alternatives=${alternatives}&access_token=${TOKEN}`);
  return d.routes || [];
}
const fmt = (r, id, risk, warnings) => ({
  id, risk_level: risk, warnings,
  distance_km: Math.round(r.distance / 100) / 10,
  duration_min: Math.round(r.duration / 60),
  geometry: r.geometry.coordinates,
});

export async function buildMockTrip(origin, destination, locale, coords = {}) {
  if (!TOKEN) return { status: 503, body: { error: 'mapbox_token_missing' } };
  const th = locale === 'th';
  try {
    const ok = (p) => Number.isFinite(p?.lat) && Number.isFinite(p?.lng);
    const [o, d] = await Promise.all([
      ok(coords.origin) ? { lat: coords.origin.lat, lng: coords.origin.lng, label: origin } : geocode(origin),
      ok(coords.destination) ? { lat: coords.destination.lat, lng: coords.destination.lng, label: destination } : geocode(destination),
    ]);
    if (!o || !d) return { status: 404, body: { error: 'location_not_found' } };
    const base = await directions([[o.lng, o.lat], [d.lng, d.lat]], true);
    const normal = base[0];
    if (!normal) return { status: 502, body: { error: 'no_route' } };
    let safe = base[1];
    if (!safe) {
      const line = normal.geometry.coordinates;
      const mid = line[Math.floor(line.length / 2)];
      const dx = d.lng - o.lng, dy = d.lat - o.lat, len = Math.hypot(dx, dy) || 1;
      safe = (await directions([[o.lng, o.lat], [mid[0] - (dy / len) * 0.1, mid[1] + (dx / len) * 0.1], [d.lng, d.lat]], false))[0];
    }
    const line = normal.geometry.coordinates;
    const mid = line[Math.floor(line.length / 2)];
    return {
      status: 200,
      body: {
        mock: true, status: 'ok', sources_used: ['Mapbox (demo)'],
        origin: o, destination: d,
        hazards: [{ lat: mid[1], lng: mid[0], label: th ? '[จำลอง] จุดเสี่ยงหิมะ/ถนนปิด' : '[MOCK] Snow / road-closure risk' }],
        routes: [
          fmt(normal, 'normal', 'WARNING', [th ? '[จำลอง] ผ่านจุดเสี่ยงหิมะ' : '[MOCK] Passes a snow-risk point']),
          fmt(safe || normal, 'safe', 'SAFE', []),
        ],
      },
    };
  } catch (err) {
    console.error('Trip mock error:', err.message);
    return { status: 503, body: { error: 'demo_unavailable' } };
  }
}
