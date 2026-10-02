// Shared by the trip form and the chat map panel. Only talks to our own /api routes.
export async function geocodeFirst(q) {
  try {
    const res = await fetch(`/api/geocode?q=${encodeURIComponent((q || '').trim())}`);
    if (!res.ok) return { error: 'unavailable' };
    const place = (await res.json()).places?.[0];
    return place ? { place } : { error: 'not_found' };
  } catch {
    return { error: 'unavailable' };
  }
}

// Resolves missing pins from the typed text (works for Thai too), then asks the backend for routes.
// Returns { data } or { error: 'input' | 'not_found' | 'timeout' | 'unavailable' }.
export async function requestTrip({ form, setForm, mode, locale, conversationId }) {
  const pos = { origin: form.originPos, destination: form.destPos };
  for (const which of ['origin', 'destination']) {
    if (pos[which]) continue;
    const g = await geocodeFirst(form[which]);
    if (g.error) return { error: g.error === 'not_found' ? 'not_found' : 'unavailable' };
    pos[which] = { lat: g.place.lat, lng: g.place.lng };
  }
  setForm((f) => ({ ...f, originPos: pos.origin, destPos: pos.destination }));

  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 58000);
  try {
    const res = await fetch('/api/trip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: conversationId,
        origin: form.origin, destination: form.destination, mode, locale,
        origin_coords: pos.origin, destination_coords: pos.destination,
        datetime: form.date && form.time ? `${form.date}T${form.time}` : null,
        preferences: { priority: form.priority, avoid_mountain: form.avoidMountain },
      }),
      signal: ctl.signal,
    });
    if (!res.ok) return { error: res.status === 404 ? 'not_found' : res.status === 400 ? 'input' : 'unavailable' };
    return { data: await res.json() };
  } catch (err) {
    return { error: err.name === 'AbortError' ? 'timeout' : 'unavailable' };
  } finally {
    clearTimeout(timer);
  }
}
