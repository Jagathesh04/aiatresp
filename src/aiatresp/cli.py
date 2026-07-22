"""Command-line interface for reproducible response generation."""

from __future__ import annotations

import argparse
from pathlib import Path

from .generator import AIAResponseGenerator
from .models import ResponseRequest
from .storage import save_npz, save_text


import sys

def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1].lower() == "info":
        sys.argv[1] = "--info"

    parser = argparse.ArgumentParser(description="Generate a Python-native AIA temperature response.")

    parser.add_argument("--emissivity-file", type=Path, help="Optional IDL SAVE file with pre-computed CHIANTI emissivity. Auto-downloaded if not provided.")
    parser.add_argument("--instrument-file", type=Path, help="Optional IDL SAVE file with instrument response. Auto-downloaded if not provided.")
    parser.add_argument("--correction-table", type=Path, help="Optional EVE correction table")
    parser.add_argument("--output", type=Path, help="Lossless .npz output")
    parser.add_argument("--text-output", type=Path, help="Optional inspectable .dat output")
    parser.add_argument("--observation-time", help="ISO timestamp for time-dependent/EVE correction")
    parser.add_argument("--fits-file", type=Path, help="Parse observation time from this FITS file header")
    parser.add_argument("--fits-dir", type=Path, help="Parse observation time automatically from a directory of AIA FITS files")
    parser.add_argument("--density", type=float, default=1e9)
    parser.add_argument("--calibration-version", default=None, help="Optional explicit calibration version (e.g. 2, 3, 4, 6, 8, 9, 10). Auto-inferred from observation date if omitted.")
    parser.add_argument("--clear-cache", action="store_true", help="Clear downloaded data cache and exit.")
    parser.add_argument("--info", action="store_true", help="Display diagnostic environment and calibration metadata.")
    args = parser.parse_args()

    if args.info:
        from .config import get_cache_dir
        cache_dir = get_cache_dir()
        cached_files = list(cache_dir.glob("*")) if cache_dir.exists() else []
        print("=" * 60)
        print("aiatresp Package Diagnostic Info")
        print("=" * 60)
        print("Package Version:        0.1.0")
        print(f"Cache Location:         {cache_dir}")
        print(f"Cached Files Count:     {len(cached_files)}")
        for f in cached_files:
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  - {f.name} ({size_mb:.1f} MB)")
        print("Default CHIANTI Ver:    9.0 (aia_V9_fullemiss.genx)")
        print("Default Calibration:    Version 10 (time-dependent)")
        print("Supported Channels:     94, 131, 171, 193, 211, 335 Angstrom")
        print("=" * 60)
        return

    if args.clear_cache:
        from .config import clear_cache
        clear_cache()
        return

    if not args.output:
        parser.error("the following arguments are required: --output (or --clear-cache)")

    obs_time = args.observation_time
    if args.fits_file:
        try:
            from astropy.io import fits
            header = fits.getheader(args.fits_file)
            obs_time = header.get("DATE-OBS") or header.get("T_OBS") or obs_time
            if obs_time:
                print(f"Parsed observation time {obs_time} from {args.fits_file}")
        except Exception as e:
            print(f"Warning: Could not parse FITS file {args.fits_file}: {e}")

    if args.fits_dir:
        print(f"Scanning directory {args.fits_dir} for best co-temporal FITS date...")
        request = ResponseRequest.from_fits_directory(
            args.fits_dir,
            emissivity_file=args.emissivity_file,
            instrument_file=args.instrument_file,
            correction_table=args.correction_table,
            electron_density_cm3=args.density,
            calibration_version=args.calibration_version,
        )
        print(f"Selected observation time: {request.observation_time}")
    else:
        request = ResponseRequest(
            emissivity_file=args.emissivity_file,
            instrument_file=args.instrument_file,
            correction_table=args.correction_table,
            observation_time=obs_time,
            electron_density_cm3=args.density,
            calibration_version=args.calibration_version,
        )
    response = AIAResponseGenerator(request).generate()
    save_npz(response, args.output)
    if args.text_output:
        save_text(response, args.text_output)


if __name__ == "__main__":
    main()
