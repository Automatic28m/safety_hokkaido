// Turns whatever the backend sends about its data sources into { weather, train, flight, traffic } states.
// Supported: service_status {name: "ok"|"degraded"|"down"} and live_sources (array of names, or {name: state}) + degraded flag.
export const SERVICES = ['weather', 'train', 'flight', 'traffic'];

const ALIASES = {
  weather: ['weather', 'jma', 'meteo'],
  train: ['train', 'jr', 'rail'],
  flight: ['flight', 'aviation', 'airport'],
  traffic: ['traffic', 'road', 'highway', 'nexco'],
};

function stateOf(v) {
  if (v === true) return 'ok';
  if (v === false) return 'down';
  const s = String(v ?? '').toLowerCase();
  if (['ok', 'active', 'live', 'up', 'online'].includes(s)) return 'ok';
  if (['degraded', 'partial', 'slow'].includes(s)) return 'degraded';
  if (['down', 'offline', 'unavailable', 'error'].includes(s)) return 'down';
  return null;
}

export function normalizeSources(data) {
  if (!data || typeof data !== 'object') return null;
  const out = {};

  const ss = data.service_status;
  if (ss && typeof ss === 'object' && !Array.isArray(ss)) {
    for (const k of SERVICES) { const st = stateOf(ss[k]); if (st) out[k] = st; }
  }

  const ls = data.live_sources;
  if (ls !== undefined && ls !== null) {
    const entries = Array.isArray(ls) ? ls.map((n) => [String(n), true]) : typeof ls === 'object' ? Object.entries(ls) : [];
    for (const k of SERVICES) {
      if (out[k]) continue;
      const hit = entries.find(([name]) => ALIASES[k].some((a) => name.toLowerCase().includes(a)));
      // listed = active; not listed = degraded when the backend says so, otherwise offline
      out[k] = hit ? stateOf(hit[1]) ?? 'ok' : data.degraded === true ? 'degraded' : 'down';
    }
  }
  return Object.keys(out).length ? out : null;
}
