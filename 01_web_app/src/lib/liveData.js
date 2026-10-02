// Functional prototypes: real, free, key-less public APIs called from our own server.
// 01 only displays these values; it does not turn them into safety decisions.
const TIMEOUT_MS = 8000;

async function getJson(url, init = {}, timeout = TIMEOUT_MS) {
  const res = await fetch(url, { ...init, signal: AbortSignal.timeout(timeout) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export function parseCoords(sp) {
  if (sp.get('lat') === null || sp.get('lng') === null) return null;
  const lat = Number(sp.get('lat')), lng = Number(sp.get('lng'));
  return Number.isFinite(lat) && Number.isFinite(lng) && Math.abs(lat) <= 90 && Math.abs(lng) <= 180 ? { lat, lng } : null;
}

export function distanceKm(lat1, lng1, lat2, lng2) {
  const rad = (d) => (d * Math.PI) / 180;
  const a = Math.sin(rad(lat2 - lat1) / 2) ** 2 + Math.cos(rad(lat1)) * Math.cos(rad(lat2)) * Math.sin(rad(lng2 - lng1) / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(a));
}

// ---- Open-Meteo: current weather + today's range for any point ----
export async function getWeather(lat, lng) {
  const url = 'https://api.open-meteo.com/v1/forecast'
    + `?latitude=${lat}&longitude=${lng}`
    + '&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m,wind_gusts_10m,snowfall,snow_depth,visibility'
    + '&daily=temperature_2m_max,temperature_2m_min,snowfall_sum&timezone=Asia%2FTokyo&wind_speed_unit=kmh';
  const d = await getJson(url, { next: { revalidate: 600 } });
  const c = d.current || {};
  const day = d.daily || {};
  return {
    location: { lat, lng },
    temperature_c: c.temperature_2m ?? null,
    feels_like_c: c.apparent_temperature ?? null,
    weather_code: c.weather_code ?? null,
    wind_kmh: c.wind_speed_10m ?? null,
    gust_kmh: c.wind_gusts_10m ?? null,
    snowfall_cm_h: c.snowfall ?? null,
    snow_depth_cm: Number.isFinite(c.snow_depth) ? c.snow_depth * 100 : null, // API gives metres
    visibility_km: Number.isFinite(c.visibility) ? c.visibility / 1000 : null, // API gives metres
    max_c: day.temperature_2m_max?.[0] ?? null,
    min_c: day.temperature_2m_min?.[0] ?? null,
    snowfall_today_cm: day.snowfall_sum?.[0] ?? null,
    observed_at: c.time ?? null,
    sources_used: ['Open-Meteo'],
  };
}

// ---- USGS: latest earthquake in a Hokkaido bounding box (+ distance from a point when given) ----
export async function getLatestQuake(point) {
  const url = 'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=1&orderby=time'
    + '&minlatitude=41&maxlatitude=46&minlongitude=139&maxlongitude=146.5';
  const d = await getJson(url, { next: { revalidate: 60 } });
  const f = d.features?.[0];
  if (!f) return { earthquake: null, sources_used: ['USGS'] };
  const [qlng, qlat, depth] = f.geometry.coordinates;
  return {
    earthquake: {
      magnitude: Number.isFinite(f.properties.mag) ? f.properties.mag : null,
      place: f.properties.place ?? null,
      time: new Date(f.properties.time).toISOString(),
      lat: qlat, lng: qlng, depth_km: depth ?? null,
      distance_km: point ? Math.round(distanceKm(point.lat, point.lng, qlat, qlng)) : null,
    },
    sources_used: ['USGS'],
  };
}

// ---- OpenStreetMap Overpass: nearest hospitals / evacuation shelters ----
const OVERPASS = ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter'];
const FILTERS = {
  hospital: ['["amenity"="hospital"]'],
  shelter: ['["emergency"="assembly_point"]', '["amenity"="shelter"]["shelter_type"!="picnic_shelter"]'],
};

export async function getNearby(lat, lng, type, radius = 5000) {
  const parts = FILTERS[type].flatMap((f) => [`node${f}(around:${radius},${lat},${lng});`, `way${f}(around:${radius},${lat},${lng});`]);
  const query = `[out:json][timeout:15];(${parts.join('')});out center 40;`;
  let data = null;
  for (const endpoint of OVERPASS) {
    try {
      data = await getJson(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `data=${encodeURIComponent(query)}`,
      }, 18000);
      break;
    } catch (err) {
      console.warn('Overpass error:', endpoint, err.message);
    }
  }
  if (!data) throw new Error('overpass_unavailable');
  const places = (data.elements || [])
    .map((el) => {
      const pLat = el.lat ?? el.center?.lat, pLng = el.lon ?? el.center?.lon;
      if (!Number.isFinite(pLat) || !Number.isFinite(pLng)) return null;
      const tags = el.tags || {};
      return {
        id: `${el.type}-${el.id}`,
        name: tags['name:en'] || tags.name || tags['name:ja'] || (type === 'hospital' ? 'Hospital' : 'Evacuation shelter'),
        type, lat: pLat, lng: pLng,
        distance_km: Math.round(distanceKm(lat, lng, pLat, pLng) * 10) / 10,
      };
    })
    .filter(Boolean)
    .sort((a, b) => a.distance_km - b.distance_km)
    .slice(0, 10);
  return { places, radius_km: radius / 1000, sources_used: ['OpenStreetMap'] };
}
