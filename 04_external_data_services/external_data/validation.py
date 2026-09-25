import re
from typing import Tuple, Optional

# Disallow control characters and URL manipulation symbols
INVALID_CHARS_PATTERN = re.compile(r"[\r\n\t\x00-\x1f\x7f<>{}|\\^~\[\]`;/?:@&=+$]")

HOKKAIDO_REGIONS = {
    "hokkaido", "all", "sapporo", "hakodate", "asahikawa", "otaru",
    "kushiro", "obihiro", "kitami", "abashiri", "nemuro", "muroran",
    "tomakomai", "niseko", "furano", "wakkanai", "rumoi", "ishikari",
    "sorachi", "shiribeshi", "iburi", "hidaka", "tokachi", "soya",
    "kamikawa", "oshima", "hiyama", "japan", "北海道"
}

KNOWN_TRAIN_LINES = {
    "all", "rapid airport", "airport", "hakodate line", "chitose line",
    "muroran line", "nemuro line", "sekisho line", "soya line",
    "sekihoku line", "senmo line", "furano line", "sassho line",
    "gakuentoshi line", "hokkaido shinkansen"
}


def validate_city(city_name: object) -> Tuple[bool, str, Optional[str]]:
    if not isinstance(city_name, str):
        return False, "", "City name must be a string."

    cleaned = city_name.strip()
    if not cleaned:
        return False, "", "City name cannot be empty."

    if len(cleaned) > 60:
        return False, "", "City name exceeds maximum permitted length (60 characters)."

    if INVALID_CHARS_PATTERN.search(cleaned):
        return False, "", "City name contains invalid or unsafe characters."

    return True, cleaned, None


def validate_region(region: object) -> Tuple[bool, str, Optional[str]]:
    if region is None:
        return True, "Hokkaido", None

    if not isinstance(region, str):
        return False, "", "Region must be a string."

    cleaned = region.strip()
    if not cleaned:
        return True, "Hokkaido", None

    if len(cleaned) > 60:
        return False, "", "Region name exceeds maximum permitted length (60 characters)."

    if INVALID_CHARS_PATTERN.search(cleaned):
        return False, "", "Region contains invalid or unsafe characters."

    lower_region = cleaned.lower()
    if lower_region not in HOKKAIDO_REGIONS and "hokkaido" not in lower_region and "北海道" not in cleaned:
        return False, cleaned, f"Region '{cleaned}' is outside the supported Hokkaido service scope."

    return True, cleaned, None


def validate_line_name(line_name: object) -> Tuple[bool, str, Optional[str]]:
    if line_name is None:
        return True, "All", None

    if not isinstance(line_name, str):
        return False, "", "Line name must be a string."

    cleaned = line_name.strip()
    if not cleaned:
        return True, "All", None

    if len(cleaned) > 80:
        return False, "", "Line name exceeds maximum permitted length (80 characters)."

    if INVALID_CHARS_PATTERN.search(cleaned):
        return False, "", "Line name contains invalid or unsafe characters."

    lower_line = cleaned.lower()
    matches_known = any(known in lower_line for known in KNOWN_TRAIN_LINES)
    if not matches_known and lower_line != "all":
        return False, cleaned, f"Train line '{cleaned}' is outside the known JR Hokkaido operational scope."

    return True, cleaned, None
