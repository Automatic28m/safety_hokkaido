from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timezone
import re

from risk_knowledge.models import RiskLevel, RiskAssessment, RouteInfo


class LocalRiskModel:
    """
    Local Risk Model Engine.
    
    Evaluates real-time risk scores and categorical risk levels (LOW, MEDIUM, HIGH)
    using multi-factor statistical and engineering rules combining disaster warnings,
    live weather conditions, and transit operational statuses.
    """

    DEFAULT_WEIGHTS = {
        "disaster": 0.45,
        "weather": 0.35,
        "transit": 0.20,
    }

    # Weather thresholds
    WIND_WHITEOUT_MS = 20.0
    WIND_SEVERE_MS = 25.0
    WIND_CAUTION_MS = 14.0
    SNOW_HEAVY_HOURLY_MM = 10.0
    TEMP_EXTREME_COLD_C = -15.0
    TEMP_SEVERE_COLD_C = -10.0

    # Risk category boundaries
    SCORE_LOW_MAX = 0.34
    SCORE_MEDIUM_MAX = 0.69

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or dict(self.DEFAULT_WEIGHTS)
        total_w = sum(self.weights.values())
        if total_w > 0:
            self.weights = {k: v / total_w for k, v in self.weights.items()}

    def _extract_dict(self, snapshot: Any) -> Optional[Dict[str, Any]]:
        if snapshot is None:
            return None
        if hasattr(snapshot, "to_dict"):
            d = snapshot.to_dict()
        elif isinstance(snapshot, dict):
            d = snapshot
        else:
            return None
        
        status = d.get("status")
        if status == "unavailable" and not d.get("data"):
            return None
        return d.get("data") if "data" in d and d.get("data") is not None else d

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Weather Risk Sub-model
    # ──────────────────────────────────────────────────────────────────────────
    def evaluate_weather_risk(
        self, weather_snapshot: Any
    ) -> Tuple[float, List[str], bool]:
        """
        Evaluates weather conditions: wind speed (whiteout risk), precipitation/snowfall,
        and freezing temperature.
        Returns: (score [0.0 - 1.0], factor_descriptions, is_available)
        """
        data = self._extract_dict(weather_snapshot)
        if not data:
            return 0.0, ["Weather data feed unavailable"], False

        current = data.get("current") or {}
        if not isinstance(current, dict):
            return 0.0, ["Weather current observation missing"], False

        score = 0.0
        factors: List[str] = []

        wind_speed = current.get("wind_speed_ms")
        temp_c = current.get("temperature_c")
        precip_mm = current.get("precipitation_total_mm")
        precip_type = current.get("precipitation_type") or "none"
        summary = str(current.get("summary") or "").lower()

        # Wind speed evaluation (Whiteout & Gale hazard)
        wind_score = 0.0
        if wind_speed is not None:
            try:
                w_val = float(wind_speed)
                if w_val >= self.WIND_SEVERE_MS:
                    wind_score = 1.0
                    factors.append(f"Severe gale wind speed ({w_val:.1f} m/s) creating extreme whiteout conditions")
                elif w_val >= self.WIND_WHITEOUT_MS:
                    wind_score = 0.85
                    factors.append(f"High wind speed ({w_val:.1f} m/s) exceeding whiteout hazard threshold (20 m/s)")
                elif w_val >= self.WIND_CAUTION_MS:
                    wind_score = 0.55
                    factors.append(f"Strong winds ({w_val:.1f} m/s) causing blowing snow and reduced visibility")
                elif w_val >= 8.0:
                    wind_score = 0.20
            except (ValueError, TypeError):
                pass

        # Precipitation & Snowfall evaluation
        precip_score = 0.0
        if precip_mm is not None:
            try:
                p_val = float(precip_mm)
                is_snow = "snow" in str(precip_type).lower() or "snow" in summary
                if is_snow:
                    if p_val >= self.SNOW_HEAVY_HOURLY_MM:
                        precip_score = 0.85
                        factors.append(f"Heavy snowfall rate ({p_val:.1f} mm/h) with rapid accumulation")
                    elif p_val >= 4.0:
                        precip_score = 0.55
                        factors.append(f"Moderate snowfall ({p_val:.1f} mm/h)")
                    elif p_val > 0.0:
                        precip_score = 0.25
                else:
                    if p_val >= 25.0:
                        precip_score = 0.70
                        factors.append(f"Heavy precipitation ({p_val:.1f} mm/h)")
                    elif p_val >= 10.0:
                        precip_score = 0.40
            except (ValueError, TypeError):
                pass

        # Temperature evaluation (Hypothermia & Freezing/Black Ice)
        temp_score = 0.0
        if temp_c is not None:
            try:
                t_val = float(temp_c)
                if t_val <= self.TEMP_EXTREME_COLD_C:
                    temp_score = 0.75
                    factors.append(f"Extreme sub-zero temperature ({t_val:.1f}°C) posing severe hypothermia hazard")
                elif t_val <= self.TEMP_SEVERE_COLD_C:
                    temp_score = 0.45
                    factors.append(f"Freezing temperature ({t_val:.1f}°C) with persistent road icing")
                elif t_val <= 0.0:
                    temp_score = 0.20
            except (ValueError, TypeError):
                pass

        # Weather summary keyword scan
        if "blizzard" in summary or "whiteout" in summary:
            wind_score = max(wind_score, 0.90)
            factors.append(f"Blizzard conditions reported in local weather summary ('{summary}')")
        elif "heavy snow" in summary:
            precip_score = max(precip_score, 0.75)

        # Composite weather score: Maximum hazard dominates, blended with secondary factors
        primary_w_hazard = max(wind_score, precip_score, temp_score)
        secondary_blend = (wind_score * 0.5) + (precip_score * 0.3) + (temp_score * 0.2)
        score = min(1.0, max(primary_w_hazard, secondary_blend))

        return score, factors, True

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Disaster Risk Sub-model (JMA Feeds)
    # ──────────────────────────────────────────────────────────────────────────
    def evaluate_disaster_risk(
        self, disaster_snapshot: Any
    ) -> Tuple[float, List[str], bool]:
        """
        Evaluates seismic activity (JMA Shindo scale) and meteorological emergency warnings.
        Returns: (score [0.0 - 1.0], factor_descriptions, is_available)
        """
        data = self._extract_dict(disaster_snapshot)
        if not data:
            return 0.0, ["Disaster data feed unavailable"], False

        quakes = data.get("earthquakes") or {}
        warnings = data.get("meteorological_warnings") or {}

        if not quakes.get("is_available", False) and not warnings.get("is_available", False):
            return 0.0, ["JMA disaster and seismic feeds unavailable"], False

        score = 0.0
        factors: List[str] = []

        # 2.1 Earthquake / Seismic Intensity
        quake_score = 0.0
        latest_event = quakes.get("latest_event")
        if latest_event and isinstance(latest_event, dict):
            shindo_str = str(latest_event.get("max_intensity") or "").strip()
            mag = latest_event.get("magnitude")
            epicenter = latest_event.get("epicenter_en") or latest_event.get("epicenter_ja") or "Hokkaido"

            # Parse JMA Shindo (1, 2, 3, 4, 5-, 5+, 6-, 6+, 7, or Japanese 5弱, 5強, etc.)
            parsed_intensity = self._parse_shindo(shindo_str)

            if parsed_intensity >= 6.0:
                quake_score = 1.0
                factors.append(f"Severe earthquake (Shindo {shindo_str}, Mag {mag}) centered at {epicenter}")
            elif parsed_intensity >= 5.0:
                quake_score = 0.90
                factors.append(f"Major earthquake (Shindo {shindo_str}, Mag {mag}) centered at {epicenter}; structural damage / aftershocks likely")
            elif parsed_intensity >= 4.0:
                quake_score = 0.50
                factors.append(f"Moderate earthquake (Shindo {shindo_str}, Mag {mag}) centered at {epicenter}")
            elif parsed_intensity >= 3.0:
                quake_score = 0.20
            elif parsed_intensity > 0:
                quake_score = 0.05

        # 2.2 Meteorological / JMA Bosai Warnings
        warning_score = 0.0
        headline = warnings.get("active_headline")
        if headline:
            h_text = str(headline).lower()
            if any(kw in h_text for kw in ["特别警报", "特別警報", "emergency warning", "tsunami", "津波", "major eruption", "噴火"]):
                warning_score = 1.0
                factors.append(f"Critical JMA Emergency Warning / Tsunami alert: '{headline}'")
            elif any(kw in h_text for kw in ["暴風雪警報", "blizzard", "大雪警報", "heavy snow warning", "暴風警報", "storm"]):
                warning_score = 0.85
                factors.append(f"JMA Severe Weather Warning active: '{headline}'")
            elif any(kw in h_text for kw in ["警報", "warning", "flood", "landslide", "土砂災害"]):
                warning_score = 0.65
                factors.append(f"JMA Weather Warning active: '{headline}'")
            elif any(kw in h_text for kw in ["注意報", "advisory"]):
                warning_score = 0.30
                factors.append(f"JMA Weather Advisory active: '{headline}'")

        score = min(1.0, max(quake_score, warning_score))
        return score, factors, True

    def _parse_shindo(self, val: str) -> float:
        if not val:
            return 0.0
        clean = val.replace("弱", "-").replace("強", "+").strip()
        if "7" in clean:
            return 7.0
        if "6+" in clean:
            return 6.5
        if "6-" in clean or "6" in clean:
            return 6.0
        if "5+" in clean:
            return 5.5
        if "5-" in clean or "5" in clean:
            return 5.0
        if "4" in clean:
            return 4.0
        if "3" in clean:
            return 3.0
        if "2" in clean:
            return 2.0
        if "1" in clean:
            return 1.0
        try:
            return float(re.findall(r"\d+", val)[0])
        except (IndexError, ValueError):
            return 0.0

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Transit Risk Sub-model
    # ──────────────────────────────────────────────────────────────────────────
    def evaluate_transit_risk(
        self, transit_snapshot: Any
    ) -> Tuple[float, List[str], List[str], bool]:
        """
        Evaluates rail / transit operational state, line suspensions, and route delays.
        Returns: (score [0.0 - 1.0], factor_descriptions, closed_segments, is_available)
        """
        data = self._extract_dict(transit_snapshot)
        if not data:
            return 0.0, ["Transit data feed unavailable"], [], False

        sim_details = data.get("simulation_details") or {}
        line_name = data.get("line_name") or "Transit Corridor"
        op_state = str(sim_details.get("operational_state") or data.get("status") or "normal").lower()
        delay_min = sim_details.get("estimated_delay_minutes", 0)
        cause = sim_details.get("cause") or "weather/track conditions"
        affected = sim_details.get("affected_section") or line_name

        score = 0.0
        factors: List[str] = []
        closed_segments: List[str] = []

        if op_state in ("suspended", "cancelled", "halted", "closed"):
            score = 1.0
            factors.append(f"Transit line '{line_name}' is fully suspended in section '{affected}' due to {cause}")
            closed_segments.append(f"{line_name} ({affected})")
        elif op_state in ("delayed", "disrupted"):
            try:
                d_val = int(delay_min)
            except (ValueError, TypeError):
                d_val = 20

            if d_val >= 60:
                score = 0.80
                factors.append(f"Severe transit disruption on '{line_name}': {d_val} min delay in section '{affected}' ({cause})")
            elif d_val >= 25:
                score = 0.50
                factors.append(f"Moderate transit delay on '{line_name}': ~{d_val} min delay in section '{affected}'")
            else:
                score = 0.25
                factors.append(f"Minor transit delay on '{line_name}': ~{d_val} min delay")
        elif op_state == "normal":
            score = 0.0
        else:
            score = 0.10

        return score, factors, closed_segments, True

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Comprehensive Multi-Factor Evaluation
    # ──────────────────────────────────────────────────────────────────────────
    def evaluate(
        self,
        weather_snapshot: Any = None,
        disaster_snapshot: Any = None,
        transit_snapshot: Any = None,
        route_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[RiskAssessment, RouteInfo]:
        """
        Evaluates combined risks and returns canonical (RiskAssessment, RouteInfo).
        Follows fail-conservative principle: missing feeds are reported clearly and
        critical single-factor emergencies guarantee a minimum HIGH risk level.
        """
        w_score, w_factors, w_avail = self.evaluate_weather_risk(weather_snapshot)
        d_score, d_factors, d_avail = self.evaluate_disaster_risk(disaster_snapshot)
        t_score, t_factors, closed_segments, t_avail = self.evaluate_transit_risk(transit_snapshot)

        # Check total availability
        available_feeds = []
        if d_avail:
            available_feeds.append("disaster")
        if w_avail:
            available_feeds.append("weather")
        if t_avail:
            available_feeds.append("transit")

        all_factors = d_factors + w_factors + t_factors

        if not available_feeds:
            # Conservative failure: completely degraded
            assessment = RiskAssessment(
                risk_level=RiskLevel.UNKNOWN,
                risk_score=0.0,
                primary_factors=["Real-time environmental and transit feeds are unavailable; risk cannot be determined safely."],
                evaluated_at=datetime.now(timezone.utc).isoformat(),
            )
            route_info = RouteInfo(
                recommended_route=None,
                alternative_routes=[],
                closed_segments=[],
            )
            return assessment, route_info

        # Re-weight dynamically among available feeds
        active_w_sum = sum(self.weights[k] for k in available_feeds)
        norm_weights = {k: self.weights[k] / active_w_sum for k in available_feeds}

        sub_scores = {
            "disaster": d_score,
            "weather": w_score,
            "transit": t_score,
        }

        weighted_score = sum(norm_weights[k] * sub_scores[k] for k in available_feeds)

        # Critical single-factor fail-safe override:
        # If an extreme disaster (tsunami/major quake) or whiteout blizzard is detected,
        # never let the risk drop below HIGH (>= 0.70).
        if d_score >= 0.85 or w_score >= 0.85:
            final_score = max(weighted_score, 0.75)
        elif t_score >= 0.90:
            final_score = max(weighted_score, 0.70)
        else:
            final_score = min(1.0, max(0.0, weighted_score))

        final_score = round(final_score, 2)

        # Map to RiskLevel
        if final_score <= self.SCORE_LOW_MAX:
            level = RiskLevel.LOW
        elif final_score <= self.SCORE_MEDIUM_MAX:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.HIGH

        if not all_factors:
            all_factors = ["Normal weather and transit conditions reported across Hokkaido."]

        assessment = RiskAssessment(
            risk_level=level,
            risk_score=final_score,
            primary_factors=all_factors,
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

        # Route evaluation
        route_info = self._compile_route_info(
            level=level,
            closed_segments=closed_segments,
            route_context=route_context,
            transit_score=t_score,
        )

        return assessment, route_info

    def _compile_route_info(
        self,
        level: RiskLevel,
        closed_segments: List[str],
        route_context: Optional[Dict[str, Any]],
        transit_score: float,
    ) -> RouteInfo:
        ctx = route_context or {}
        origin = ctx.get("origin") or ctx.get("start_city") or "Sapporo"
        dest = ctx.get("destination") or ctx.get("destination_city") or "New Chitose Airport"

        if closed_segments:
            recommended = f"Alternative highway bus / detour corridor between {origin} and {dest}"
            alternatives = [
                f"Expressway detour corridor ({origin} - {dest})",
                "Scheduled regional express bus",
            ]
        elif level == RiskLevel.HIGH:
            recommended = f"Direct main transit line ({origin} - {dest}) with extreme caution"
            alternatives = [
                f"Wait for weather advisory clearance at {origin} terminal",
                "Sheltered express rail service if operating",
            ]
        elif level == RiskLevel.MEDIUM:
            recommended = f"Standard rail / expressway line between {origin} and {dest}"
            alternatives = [
                f"Secondary scenic highway route ({origin} - {dest})",
            ]
        else:
            recommended = f"Standard direct express corridor between {origin} and {dest}"
            alternatives = [
                f"Local rail service ({origin} - {dest})",
            ]

        return RouteInfo(
            recommended_route=recommended,
            alternative_routes=alternatives,
            closed_segments=closed_segments,
        )
