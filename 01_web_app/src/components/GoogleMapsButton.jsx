"use client";

import { useTranslations } from "next-intl";

// Google Maps' routing API needs billing, so we hand the trip to the user's free Google Maps app/site.
const TRAVEL_MODE = { train: "transit", bus: "transit", car: "driving" };
const point = (text, pos) => (pos ? `${pos.lat},${pos.lng}` : (text || "").trim());

export default function GoogleMapsButton({ mode = "train", origin, destination, originPos, destPos, className = "" }) {
  const t = useTranslations("Trip");
  const o = point(origin, originPos);
  const d = point(destination, destPos);
  const base = `inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-bold ${className}`;

  if (!o || !d) {
    return <span aria-disabled="true" className={`${base} bg-gray-200 text-gray-500 cursor-not-allowed`}>🧭 {t("googleMaps")}</span>;
  }
  const href = `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(o)}&destination=${encodeURIComponent(d)}&travelmode=${TRAVEL_MODE[mode] || "driving"}`;
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={`${base} bg-[#0047b3] text-white hover:bg-[#003a94] transition-colors`}>
      🧭 {t("googleMaps")}
    </a>
  );
}
