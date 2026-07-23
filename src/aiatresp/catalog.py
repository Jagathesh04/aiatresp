"""Dynamic SSW AIA calibration catalog parser and version resolver."""

from __future__ import annotations

import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .config import get_cache_dir

SSW_RESPONSE_URL = "https://hesperia.gsfc.nasa.gov/ssw/sdo/aia/response/"
SOHO_RESPONSE_URL = "https://soho.nascom.nasa.gov/solarsoft/sdo/aia/response/"
CATALOG_FILENAME = "catalog_cache.json"

DEFAULT_BUILTIN_CATALOG: List[Dict[str, str]] = [
    {"version": "preflight", "timestamp": "2010-05-01T00:00:00+00:00"},
    {"version": "2", "timestamp": "2011-11-29T00:00:00+00:00"},
    {"version": "3", "timestamp": "2012-09-26T20:12:21+00:00"},
    {"version": "4", "timestamp": "2013-01-09T20:48:35+00:00"},
    {"version": "6", "timestamp": "2014-05-09T02:58:12+00:00"},
    {"version": "6", "timestamp": "2014-10-27T23:00:30+00:00"},
    {"version": "7", "timestamp": "2017-11-29T19:56:26+00:00"},
    {"version": "8", "timestamp": "2017-11-30T05:11:27+00:00"},
    {"version": "8", "timestamp": "2017-12-10T05:06:27+00:00"},
    {"version": "9", "timestamp": "2020-07-06T21:54:52+00:00"},
    {"version": "10", "timestamp": "2020-10-28T18:00:00+00:00"},
    {"version": "10", "timestamp": "2020-10-28T19:00:00+00:00"},
    {"version": "10", "timestamp": "2020-11-19T19:00:00+00:00"},
]




def fetch_remote_catalog() -> List[Dict[str, str]]:
    """Dynamically fetch and parse the SSW AIA calibration release catalog from primary/mirror NASA indices."""
    urls = [SSW_RESPONSE_URL, SOHO_RESPONSE_URL]
    last_err = None

    for url in urls:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "aiatresp/0.1.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html = resp.read().decode("utf-8", errors="ignore")

                pattern = r'aia_([A-Za-z0-9]+)_(\d{8})_(\d{6})_response_table\.txt'
                matches = re.findall(pattern, html)

                if not matches:
                    continue

                entries = []
                seen = set()

                for ver_raw, dstr, tstr in matches:
                    dt = datetime.strptime(f"{dstr}{tstr}", "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
                    ver_clean = ver_raw.lstrip("Vv")
                    key = (ver_clean, dt.isoformat())
                    if key not in seen:
                        seen.add(key)
                        entries.append({"version": ver_clean, "timestamp": dt.isoformat()})

                entries.sort(key=lambda x: datetime.fromisoformat(x["timestamp"]))
                return entries
            except Exception as e:
                last_err = e
                time.sleep(1 + attempt)

    raise RuntimeError(f"Failed to fetch remote catalog from all mirrors: {last_err}")


def get_ssw_catalog(refresh: bool = False) -> List[Dict[str, str]]:
    """Get the SSW calibration catalog dynamically from cache, remote network index, or built-in fallback."""
    cache_path = get_cache_dir() / CATALOG_FILENAME

    if not refresh and cache_path.exists():
        try:
            with cache_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass

    try:
        catalog = fetch_remote_catalog()
        with cache_path.open("w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2)
        return catalog
    except Exception:
        if cache_path.exists():
            try:
                with cache_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        return data
            except Exception:
                pass
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with cache_path.open("w", encoding="utf-8") as f:
                json.dump(DEFAULT_BUILTIN_CATALOG, f, indent=2)
        except Exception:
            pass
        return DEFAULT_BUILTIN_CATALOG




def resolve_calibration_version_from_date(obstime: str | datetime) -> int | str:
    """Dynamically resolve the exact AIA calibration version for a given observation timestamp."""
    if isinstance(obstime, str):
        s = obstime.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
    else:
        dt = obstime

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    catalog = get_ssw_catalog()
    
    # Sort entries chronologically
    sorted_entries = []
    for item in catalog:
        item_dt = datetime.fromisoformat(item["timestamp"])
        if item_dt.tzinfo is None:
            item_dt = item_dt.replace(tzinfo=timezone.utc)
        sorted_entries.append((item_dt, item["version"]))

    sorted_entries.sort(key=lambda x: x[0])

    if not sorted_entries or dt < sorted_entries[0][0]:
        return "preflight"

    selected_version = sorted_entries[0][1]
    for rel_time, ver in sorted_entries:
        if rel_time <= dt:
            selected_version = ver
        else:
            break

    if selected_version.isdigit():
        return int(selected_version)
    return selected_version.lower()


def resolve_genx_filenames(version: int | str) -> Tuple[str, str]:
    """Map calibration version to SolarSoft GENX emissivity and instrument filenames."""
    if isinstance(version, str):
        v_clean = version.strip().lower()
        if v_clean == "preflight":
            return ("aia_preflight_fullemiss.genx", "aia_preflight_all_fullinst.genx")
        if v_clean.isdigit():
            v = int(v_clean)
        else:
            raise ValueError(f"Invalid calibration_version '{version}'. Must be an integer or 'preflight'.")
    elif isinstance(version, int):
        v = version
    else:
        raise ValueError(f"Invalid calibration_version type '{type(version).__name__}'.")

    if v in (9, 10):
        v_str = "9"
    elif v in (7, 8):
        v_str = "8"
    elif v in (5, 6):
        v_str = "6"
    elif v == 4:
        v_str = "4"
    elif v == 3:
        v_str = "3"
    elif v in (1, 2):
        v_str = "2"
    else:
        raise ValueError(f"Unsupported calibration_version {version}. Valid versions are 1 to 10 or 'preflight'.")

    return (f"aia_V{v_str}_fullemiss.genx", f"aia_V{v_str}_all_fullinst.genx")
