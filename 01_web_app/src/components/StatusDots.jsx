"use client";

import { useTranslations } from "next-intl";
import { useTrip } from "./TripContext";
import { SERVICES } from "@/lib/sourceStatus";

// green = active, yellow = degraded, dark grey = offline, light grey = not known yet
const DOT = { ok: "bg-green-500", degraded: "bg-yellow-400", down: "bg-gray-500", unknown: "bg-gray-300" };

export default function StatusDots({ className = "", labelClass = "inline" }) {
  const t = useTranslations("Status");
  const { sourceStatus } = useTrip();

  return (
    <div role="group" aria-label={t("title")} className={`flex items-center flex-wrap gap-x-3 gap-y-1 ${className}`}>
      {SERVICES.map((k) => {
        const st = sourceStatus[k] || "unknown";
        const tip = `${t(`services.${k}`)}: ${t(`state.${st}`)}`;
        return (
          <span key={k} title={tip} aria-label={tip} className="flex items-center gap-1.5">
            <i className={`inline-block w-2.5 h-2.5 rounded-full ring-1 ring-white/70 ${DOT[st]}`} />
            <span className={labelClass}>{t(`services.${k}`)}</span>
          </span>
        );
      })}
    </div>
  );
}
