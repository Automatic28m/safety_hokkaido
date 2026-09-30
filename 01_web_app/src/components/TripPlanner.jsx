"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations, useLocale } from "next-intl";
import MapUI from "./MapUI";
import { useTrip } from "./TripContext";

const RISK_STYLE = { SAFE: "bg-green-700", WARNING: "bg-amber-500", AVOID_TRAVEL: "bg-red-600" };
const SWATCH = {
  normal: "border-t-4 border-dashed border-orange-500",
  safe: "border-t-4 border-solid border-green-700",
};
const inputCls = "w-full border-2 border-black rounded-xl px-3 py-2 bg-white text-black outline-none focus:border-orange-500";
const POS_KEY = { origin: "originPos", destination: "destPos" };

async function reverseName(pos) {
  try {
    const res = await fetch(`/api/geocode?lat=${pos.lat}&lng=${pos.lng}`);
    if (res.ok) {
      const data = await res.json();
      if (data.places?.[0]?.place_name) return data.places[0].place_name;
    }
  } catch { /* fall through */ }
  return `${pos.lat.toFixed(5)}, ${pos.lng.toFixed(5)}`;
}

function LocationInput({ value, onType, onPick, onLocate, locating, placeholder, locateTitle, unavailableText }) {
  const [suggestions, setSuggestions] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  const wrapperRef = useRef(null);
  const timerRef = useRef(null);
  const abortRef = useRef(null);

  useEffect(() => {
    const onDown = (e) => { if (wrapperRef.current && !wrapperRef.current.contains(e.target)) setIsOpen(false); };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  const handleType = (val) => {
    onType(val);
    setIsOpen(true);
    
    if (timerRef.current) clearTimeout(timerRef.current);
    if (abortRef.current) abortRef.current.abort();

    if (!val || val.trim().length < 2) { 
      setSuggestions([]); 
      return; 
    }
    
    timerRef.current = setTimeout(async () => {
      abortRef.current = new AbortController();
      try {
        const res = await fetch(`/api/geocode?q=${encodeURIComponent(val.trim())}`, { signal: abortRef.current.signal });
        if (!res.ok) throw new Error(String(res.status));
        const data = await res.json();
        setSuggestions(data.places || []);
        setFailed(false);
      } catch (err) {
        if (err.name !== "AbortError") { setSuggestions([]); setFailed(true); }
      }
    }, 400);
  };

  const pick = (s) => { onPick(s); setIsOpen(false); setSuggestions([]); setFailed(false); };

  return (
    <div className="w-full mt-1" ref={wrapperRef}>
      <div className="relative w-full flex items-center">
        <input
          type="text"
          className="w-full border-2 border-black rounded-xl pl-3 pr-10 py-2 bg-white text-black outline-none focus:border-[#0047b3] transition-colors disabled:bg-gray-100"
          value={value}
          disabled={locating}
          onChange={(e) => handleType(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && isOpen && suggestions[0]) { e.preventDefault(); pick(suggestions[0]); } }}
          placeholder={placeholder}
          maxLength={200}
          autoComplete="off"
        />
        <button
          type="button"
          onClick={onLocate}
          disabled={locating}
          title={locateTitle}
          aria-label={locateTitle}
          className="absolute right-2 p-1.5 text-[#0047b3] hover:bg-blue-100 rounded-full transition-colors disabled:opacity-50"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="3 11 22 2 13 21 11 13 3 11" />
          </svg>
        </button>

        {isOpen && suggestions.length > 0 && (
          <ul className="absolute top-full left-0 right-0 mt-1 bg-white border-2 border-black rounded-xl shadow-xl z-50 max-h-60 overflow-y-auto">
            {suggestions.map((s) => (
              <li
                key={s.id}
                className="px-4 py-2 hover:bg-orange-100 cursor-pointer text-sm text-black border-b last:border-b-0 border-gray-100 transition-colors"
                onClick={() => pick(s)}
              >
                <div className="font-bold">{s.text}</div>
                <div className="text-xs text-gray-500 truncate">{s.place_name}</div>
              </li>
            ))}
          </ul>
        )}
      </div>
      {failed && isOpen && <p className="text-xs font-normal text-amber-700 mt-1">{unavailableText}</p>}
    </div>
  );
}

export default function TripPlanner({ mode = "train" }) {
  const t = useTranslations("Trip");
  const locale = useLocale();
  const { conversationId, form, setForm, result, setResult, applyBackendTrip } = useTrip();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [info, setInfo] = useState(null);
  const [locating, setLocating] = useState(null); 
  const [fitTick, setFitTick] = useState(0); 
  const [visible, setVisible] = useState({ normal: true, safe: true });
  const [focusId, setFocusId] = useState(null);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));
  const swap = () => setForm((f) => ({ ...f, origin: f.destination, destination: f.origin, originPos: f.destPos, destPos: f.originPos }));

  const update = (which, text, pos) => setForm((f) => ({ ...f, [which]: text, [POS_KEY[which]]: pos }));
  const onType = (which) => (text) => update(which, text, null);
  const onPick = (which) => (place) => {
    update(which, place.place_name, { lat: place.lat, lng: place.lng });
    setFitTick((n) => n + 1);
    setInfo(null);
  };

  const onPinMove = async (which, pos) => {
    setForm((f) => ({ ...f, [POS_KEY[which]]: pos }));
    setResult(null); 
    setInfo(t("pinMoved"));
    const name = await reverseName(pos);
    setForm((f) => ({ ...f, [which]: name }));
  };

  const locate = (which) => {
    if (!navigator.geolocation) return setError(t("errorGeoUnsupported"));
    setError(null);
    setLocating(which);
    navigator.geolocation.getCurrentPosition(
      async (p) => {
        const pos = { lat: p.coords.latitude, lng: p.coords.longitude };
        const name = await reverseName(pos);
        update(which, name, pos);
        setFitTick((n) => n + 1);
        setLocating(null);
      },
      () => { setLocating(null); setError(t("errorGeoDenied")); },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!form.origin.trim() || !form.destination.trim()) return setError(t("errorInput"));
    setLoading(true); setError(null); setInfo(null); setResult(null); setFocusId(null);
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), 58000);
    try {
      const res = await fetch("/api/trip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          conversation_id: conversationId,
          origin: form.origin, destination: form.destination, mode, locale,
          origin_coords: form.originPos, destination_coords: form.destPos,
          datetime: form.date && form.time ? `${form.date}T${form.time}` : null,
          preferences: { priority: form.priority, avoidMountain: form.avoidMountain },
        }),
        signal: ctl.signal,
      });
      if (!res.ok) return setError(res.status === 404 ? t("errorNotFound") : res.status === 400 ? t("errorInput") : t("errorUnavailable"));
      const data = await res.json();
      if (!applyBackendTrip(data)) return setError(t("errorNoRoute"));
      
      // Reset visibility and focus when new results arrive
      setVisible({ normal: true, safe: true });
      setFocusId(null);
    } catch (err) {
      setError(err.name === "AbortError" ? t("errorTimeout") : t("errorUnavailable"));
    } finally {
      clearTimeout(timer);
      setLoading(false);
    }
  };

  const duration = (min) => (min >= 60 ? t("durationHrMin", { h: Math.floor(min / 60), m: min % 60 }) : t("durationMin", { m: min }));

  return (
    <div className="space-y-5">
      <form onSubmit={submit} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="font-bold text-sm text-black flex flex-col">
          {t("from")}
          <LocationInput
            value={form.origin}
            onType={onType("origin")}
            onPick={onPick("origin")}
            onLocate={() => locate("origin")}
            locating={locating === "origin"}
            placeholder={locating === "origin" ? t("locating") : t("fromPlaceholder")}
            locateTitle={t("locate")}
            unavailableText={t("searchUnavailable")}
          />
        </div>

        <div className="font-bold text-sm text-black flex flex-col">
          <span className="flex items-center justify-between">
            {t("to")}
            <button type="button" onClick={swap} aria-label={t("swap")} className="text-xs font-bold text-[#0047b3] hover:underline">⇄ {t("swap")}</button>
          </span>
          <LocationInput
            value={form.destination}
            onType={onType("destination")}
            onPick={onPick("destination")}
            onLocate={() => locate("destination")}
            locating={locating === "destination"}
            placeholder={locating === "destination" ? t("locating") : t("toPlaceholder")}
            locateTitle={t("locate")}
            unavailableText={t("searchUnavailable")}
          />
        </div>

        <label className="font-bold text-sm text-black">{t("date")}
          <input type="date" className={`${inputCls} mt-1`} value={form.date} onChange={set("date")} />
        </label>
        <label className="font-bold text-sm text-black">{t("time")}
          <input type="time" className={`${inputCls} mt-1`} value={form.time} onChange={set("time")} />
        </label>
        <label className="font-bold text-sm text-black">{t("priority")}
          <select className={`${inputCls} mt-1`} value={form.priority} onChange={set("priority")}>
            <option value="safest">{t("prioritySafest")}</option>
            <option value="fastest">{t("priorityFastest")}</option>
          </select>
        </label>
        <label className="flex items-center gap-2 font-bold text-sm text-black sm:mt-6">
          <input type="checkbox" className="w-5 h-5 accent-green-700" checked={form.avoidMountain} onChange={set("avoidMountain")} />
          {t("avoidMountain")}
        </label>
        <button type="submit" disabled={loading} className="sm:col-span-2 bg-orange-400 hover:bg-orange-500 disabled:opacity-60 text-white text-lg font-bold rounded-xl py-3 mt-2 shadow-md transition-all active:scale-[0.98]">
          {loading ? t("searching") : t("search")}
        </button>
      </form>

      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 text-red-800 px-4 py-3 text-sm">{error}</div>}
      {info && <div role="status" className="rounded-xl border border-blue-200 bg-blue-50 text-blue-900 px-4 py-3 text-sm">{info}</div>}

      <MapUI
        routes={result?.routes || []}
        hazards={result?.hazards || []}
        pins={{ origin: form.originPos, destination: form.destPos }}
        onPinMove={onPinMove}
        pinLabels={{ origin: t("pinA"), destination: t("pinB") }}
        fitTick={fitTick}
        visible={visible}
        focusId={focusId}
        noTokenText={t("noToken")}
      />
      {(form.originPos || form.destPos) && <p className="text-xs text-gray-600">📍 {t("pinHint")}</p>}

      {result && (
        <div className="space-y-3">
          {result.mock && <p className="text-xs font-bold text-amber-700">⚠️ {t("demoBadge")}</p>}
          {result.status === "degraded" && <p className="text-xs font-bold text-amber-700">⚠️ {t("degraded")}</p>}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {result.routes.map((r) => (
              <div key={r.id} className={`rounded-2xl border-2 p-4 ${focusId === r.id ? "border-black" : "border-gray-200"} bg-white shadow-sm`}>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 font-bold text-black">
                    <span className={`inline-block w-8 ${SWATCH[r.id] || SWATCH.normal}`} />
                    {t(`route.${r.id}`)}
                  </div>
                  {RISK_STYLE[r.risk_level] && <span className={`text-xs text-white font-bold rounded-lg px-2 py-1 ${RISK_STYLE[r.risk_level]}`}>{t(`risk.${r.risk_level}`)}</span>}
                </div>
                <div className="text-sm text-gray-700">
                  {r.distance_km != null && <span className="mr-4">{r.distance_km} km</span>}
                  {r.duration_min != null && <span>{duration(r.duration_min)}</span>}
                </div>
                {r.warnings?.length > 0 && (
                  <ul className="list-disc pl-5 mt-2 text-sm text-gray-700 space-y-1">
                    {r.warnings.map((w, i) => <li key={i}>{w}</li>)}
                  </ul>
                )}
                <div className="flex items-center gap-4 mt-3 text-sm">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input type="checkbox" checked={visible[r.id] !== false} onChange={(e) => setVisible((v) => ({ ...v, [r.id]: e.target.checked }))} className="w-4 h-4 accent-green-700" />
                    {t("show")}
                  </label>
                  <button type="button" onClick={() => setFocusId(focusId === r.id ? null : r.id)} className="font-bold text-[#0047b3] hover:underline">
                    {focusId === r.id ? t("showAll") : t("zoomTo")}
                  </button>
                </div>
              </div>
            ))}
          </div>
          {result.sources_used?.length > 0 && (
            <p className="text-xs text-gray-500">{t("sources")}: {result.sources_used.map((s) => (typeof s === "string" ? s : s.name)).join(", ")}</p>
          )}
        </div>
      )}
    </div>
  );
}