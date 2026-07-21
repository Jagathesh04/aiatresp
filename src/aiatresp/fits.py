from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union
import re
from astropy.io import fits


def parse_date_from_directory(data_dir: Union[str, Path]) -> datetime:
    """Scan a directory of AIA FITS files and determine the best co-temporal observation time.
    
    This matches the 6 core AIA EUV channels to find the most representative DATE-OBS.
    """
    data_dir = str(data_dir)
    entries = []
    
    AIA_CHANNELS = (94, 131, 171, 193, 211, 335)
    
    for fn in os.listdir(data_dir):
        if not fn.lower().endswith((".fits", ".fts")):
            continue
        path = os.path.join(data_dir, fn)
        try:
            with fits.open(path, memmap=False) as hdul:
                if len(hdul) > 1:
                    try:
                        h = hdul[1].header
                    except Exception:
                        h = hdul[0].header
                else:
                    h = hdul[0].header
                h0 = hdul[0].header

            wl_raw = h.get("WAVELNTH") or h.get("WAVE_STR") or h0.get("WAVELNTH") or h0.get("WAVE_STR")
            wl = None
            if wl_raw is not None:
                try:
                    wl = int(round(float(str(wl_raw).split("_")[0])))
                except (ValueError, IndexError):
                    pass

            if wl is None:
                for channel in AIA_CHANNELS:
                    pattern = rf"(?:^|[._])0*{channel}(?:[._A]|$)"
                    if re.search(pattern, fn):
                        wl = channel
                        break
                        
            if wl not in AIA_CHANNELS:
                continue
                
            date_str = h.get("DATE-OBS") or h.get("DATE_OBS")
            if not date_str:
                continue
                
            s = str(date_str).strip()
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
                
            entries.append({"wavelength": wl, "datetime": dt})
        except Exception:
            continue
            
    if not entries:
        raise ValueError(f"No valid AIA FITS files found in {data_dir} for channels {AIA_CHANNELS}")
        
    per_wl = {wl: [] for wl in AIA_CHANNELS}
    for e in entries:
        per_wl[e["wavelength"]].append(e)

    missing = [wl for wl in AIA_CHANNELS if not per_wl[wl]]
    if missing:
        all_times = sorted([e["datetime"] for e in entries])
        return all_times[len(all_times) // 2]
        
    all_candidates = sorted(entries, key=lambda x: x["datetime"])
    best = None
    best_key = None
    for anchor in all_candidates:
        t0 = anchor["datetime"]
        deltas = []
        for wl in AIA_CHANNELS:
            nearest = min(per_wl[wl], key=lambda x: abs((x["datetime"] - t0).total_seconds()))
            deltas.append(abs((nearest["datetime"] - t0).total_seconds()))
        key = (sum(deltas), max(deltas))
        if best_key is None or key < best_key:
            best_key = key
            best = t0
            
    return best
