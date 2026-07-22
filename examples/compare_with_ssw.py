#!/usr/bin/env python3
"""
Scientific Verification Script for aiatresp
-------------------------------------------
Computes numerical error metrics (Max Relative Error %, RMS Error) 
comparing aiatresp against official SolarSoft (SSW) reference tables.
"""

from pathlib import Path
import numpy as np
from aiatresp import ResponseRequest, AIAResponseGenerator


def main() -> None:
    print("=" * 75)
    print("aiatresp Scientific Verification against SSW Reference Standards")
    print("=" * 75)

    # Calculate Version 9 response without time-degradation for direct table comparison
    req_v9 = ResponseRequest(calibration_version=9, observation_time=None)
    resp = AIAResponseGenerator(req_v9).generate()

    print(f"Generated Channels:    {resp.channels}")
    print(f"Temperature Grid Points: {len(resp.logt)} points (log10(T) = {resp.logt[0]:.2f} to {resp.logt[-1]:.2f})")
    print(f"Units:                 {resp.units}")

    ref_path = Path(__file__).parent.parent / "comparison" / "data" / "aia_tresp_latest.dat"
    if not ref_path.exists():
        ref_path = Path("/home/jagathesh/final/UPF_DEM_Project/data/aia_tresp_latest.dat")

    if ref_path.exists():
        import scipy.io as sio
        ref_data = sio.readsav(ref_path)
        ref_tr = ref_data["tr"]  # shape (6, 101)

        print("\nNumerical Verification Metrics:")
        print("=" * 75)
        print(f"{'Channel':<10} | {'Peak Value':<14} | {'RMSE':<14} | {'Max Rel Error (%)':<18} | {'Correlation':<12}")
        print("-" * 75)

        for i, ch in enumerate(resp.channels):
            gen_vals = resp.response[i]
            ref_vals = ref_tr[i]

            max_ref = np.max(ref_vals)
            mask = ref_vals > (0.01 * max_ref)

            rmse = np.sqrt(np.mean((gen_vals - ref_vals) ** 2))
            rel_err = np.max(np.abs(gen_vals[mask] - ref_vals[mask]) / ref_vals[mask]) * 100.0 if np.any(mask) else 0.0
            corr = np.corrcoef(gen_vals, ref_vals)[0, 1]

            print(f"{ch:<10} | {max_ref:<14.4e} | {rmse:<14.4e} | {rel_err:<18.2f}% | {corr:<12.6f}")

        print("=" * 75)
        print("Verification completed successfully.")
    else:
        print(f"\nNote: Reference IDL file not found at {ref_path}. Standard calculation executed cleanly.")


if __name__ == "__main__":
    main()
