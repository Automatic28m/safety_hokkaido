"use client";

import { useEffect, useRef, useState } from "react";
import Map, { Marker, NavigationControl, Source, Layer } from "react-map-gl";
import "mapbox-gl/dist/mapbox-gl.css"; // required, otherwise the map layout breaks

const TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
// normal = orange dashed, safe (hazard-avoiding) = green solid
const LINE = {
  normal: { color: "#f97316", width: 5, dash: [2, 1.5] },
  safe: { color: "#15803d", width: 6, dash: null },
};

function boundsOf(lines) {
  const pts = lines.flat();
  if (!pts.length) return null;
  const lngs = pts.map((p) => p[0]);
  const lats = pts.map((p) => p[1]);
  return [[Math.min(...lngs), Math.min(...lats)], [Math.max(...lngs), Math.max(...lats)]];
}

export default function MapUI({
  routes = [], hazards = [], visible = {}, focusId = null,
  pins = {}, onPinMove, pinLabels = {}, fitTick = 0,
  noTokenText = "Map token is missing",
}) {
  const mapRef = useRef(null);
  const [viewState, setViewState] = useState({ longitude: 141.3544, latitude: 43.0618, zoom: 9 });

  // Zoom to the routes whenever results (or the focused route) change
  useEffect(() => {
    const lines = routes.filter((r) => !focusId || r.id === focusId).map((r) => r.geometry).filter((g) => g?.length > 1);
    const b = boundsOf(lines);
    if (b && mapRef.current) mapRef.current.fitBounds(b, { padding: 60, duration: 800 });
  }, [routes, focusId]);

  // Fly to the pin(s) when a place is picked or GPS is used (not while the user drags a pin)
  useEffect(() => {
    if (!fitTick || !mapRef.current) return;
    const pts = [pins.origin, pins.destination].filter(Boolean).map((p) => [p.lng, p.lat]);
    if (pts.length === 1) mapRef.current.flyTo({ center: pts[0], zoom: 12, duration: 800 });
    else if (pts.length === 2) mapRef.current.fitBounds(boundsOf([pts]), { padding: 90, maxZoom: 14, duration: 800 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fitTick]);

  if (!TOKEN) {
    return (
      <div className="w-full min-h-[360px] rounded-xl border-2 border-dashed border-gray-300 bg-gray-100 flex items-center justify-center text-gray-600 text-center p-6">
        {noTokenText} (NEXT_PUBLIC_MAPBOX_TOKEN)
      </div>
    );
  }

  const ordered = [...routes].sort((a) => (a.id === "safe" ? 1 : -1)); // safe route drawn on top

  return (
    <div className="w-full h-[380px] md:h-[480px] rounded-xl overflow-hidden shadow-inner relative border-2 border-gray-300">
      <Map
        ref={mapRef}
        {...viewState}
        onMove={(evt) => setViewState(evt.viewState)}
        mapStyle="mapbox://styles/mapbox/streets-v12"
        mapboxAccessToken={TOKEN}
      >
        <NavigationControl position="bottom-right" />

        {ordered.map((r) => {
          const st = LINE[r.id] || LINE.normal;
          if (visible[r.id] === false || !(r.geometry?.length > 1)) return null;
          return (
            <Source key={r.id} id={`src-${r.id}`} type="geojson" data={{ type: "Feature", geometry: { type: "LineString", coordinates: r.geometry } }}>
              <Layer
                id={`line-${r.id}`}
                type="line"
                layout={{ "line-cap": "round", "line-join": "round" }}
                paint={{
                  "line-color": st.color,
                  "line-width": st.width,
                  "line-opacity": focusId && focusId !== r.id ? 0.3 : 0.95,
                  ...(st.dash ? { "line-dasharray": st.dash } : {}),
                }}
              />
            </Source>
          );
        })}

        {hazards.map((h, i) => (
          <Marker key={i} longitude={h.lng} latitude={h.lat}>
            <div title={h.label} className="w-7 h-7 rounded-full bg-red-600 text-white font-black border-2 border-white shadow flex items-center justify-center">!</div>
          </Marker>
        ))}

        {/* Draggable A / B pins: drag to set the exact position */}
        {[["origin", "A", "bg-[#0047b3]"], ["destination", "B", "bg-orange-500"]].map(([key, letter, bg]) =>
          pins[key] ? (
            <Marker
              key={key}
              longitude={pins[key].lng}
              latitude={pins[key].lat}
              draggable
              onDragEnd={(e) => onPinMove?.(key, { lat: e.lngLat.lat, lng: e.lngLat.lng })}
            >
              <div title={pinLabels[key]} className={`w-9 h-9 rounded-full ${bg} text-white font-bold text-lg border-[3px] border-white shadow-lg flex items-center justify-center cursor-grab active:cursor-grabbing`}>{letter}</div>
            </Marker>
          ) : null
        )}
      </Map>
    </div>
  );
}
