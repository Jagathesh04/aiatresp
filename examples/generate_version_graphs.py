"""Generate side-by-side comparison graphs for all AIA calibration versions (IDL vs aiatresp).

This script generates .dat files via IDL for versions 1, 2, 3, 4, 8, 9, and 10,
computes the matching aiatresp Python response, and saves individual comparison plots
for each version in docs/version_plots/.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import scipy.io

from aiatresp import aia_response

IDL_PATH = r"C:\Program Files\Exelis\IDL85\bin\bin.x86\idl.exe"

# Calibration version matrix and representative dates
VERSION_MATRIX = [
    {"version": 1, "name": "v1_preflight", "title": "Version 1 (Pre-flight)", "date": "2010-06-01T00:00:00"},
    {"version": 2, "name": "v2_2011", "title": "Version 2 (Epoch 2011)", "date": "2011-01-01T00:00:00"},
    {"version": 3, "name": "v3_2012", "title": "Version 3 (Epoch 2012)", "date": "2012-01-01T00:00:00"},
    {"version": 4, "name": "v4_2013", "title": "Version 4 (Epoch 2013)", "date": "2013-01-01T00:00:00"},
    {"version": 8, "name": "v8_2017", "title": "Version 8 (Epoch 2017)", "date": "2017-01-01T00:00:00"},
    {"version": 9, "name": "v9_2019", "title": "Version 9 (Epoch 2019)", "date": "2019-01-01T00:00:00"},
    {"version": 10, "name": "v10_2024", "title": "Version 10 (Epoch 2024)", "date": "2024-01-01T00:00:00"},
]

OUT_DIR = Path(__file__).parent.parent / "docs" / "version_plots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_idl_dat(case: dict) -> Path:
    """Generate IDL reference .dat file using SSW IDL aia_get_response."""
    dat_path = OUT_DIR / f"idl_{case['name']}.dat"
    batch_path = OUT_DIR / f"run_{case['name']}.batch"
    
    idl_code = f"""
setenv,'SSW=C:\\ssw'
setenv,'SSWDB=C:\\sswdb'
@C:\\ssw\\gen\\idl\\ssw_system\\idl_startup_windows.pro
ssw_path,/aia,/chianti,/quiet
t = aia_get_response(version={case['version']}, timedepend_date='{case['date']}', /temperature, /dn, /eve, /silent)
ids = [0,1,2,3,4,6]
channels = t.channels[ids]
logt = t.logte
tr = t.all[*,ids]
units = t.units
save, file='{str(dat_path)}', channels, logt, tr, units
exit
"""
    with open(batch_path, "w") as f:
        f.write(idl_code)

    cmd = [IDL_PATH, "-e", f"@{str(batch_path)}"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if not dat_path.exists():
        raise RuntimeError(f"IDL execution failed for {case['name']}:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return dat_path


def generate_plot(case: dict, idl_tr: np.ndarray, py_resp) -> Path:
    """Generate and save side-by-side comparison plot for a specific version."""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    channels = py_resp.channels
    logt = py_resp.logt
    py_tr = py_resp.response  # shape: (6, 101)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

    for i, ch in enumerate(channels):
        # IDL baseline curve (dashed line)
        ax.plot(logt, idl_tr[i, :], "--", color=colors[i], alpha=0.75, linewidth=1.8, label=f"{ch} Å (IDL float32)")
        # Python curve (solid line)
        ax.plot(logt, py_tr[i, :], "-", color=colors[i], linewidth=1.4, label=f"{ch} Å (aiatresp float64)")

    # Calculate metrics
    abs_diff = np.abs(idl_tr - py_tr)
    max_abs_diff = np.max(abs_diff)
    rmse = np.sqrt(np.mean(abs_diff ** 2))
    
    nonzero_mask = idl_tr > 0
    max_rel_diff = np.max(abs_diff[nonzero_mask] / idl_tr[nonzero_mask]) if np.any(nonzero_mask) else 0.0

    ax.set_yscale("log")
    ax.set_xlim(4.0, 9.0)
    ax.set_ylim(1e-28, 1e-23)
    ax.set_xlabel(r"$\log_{10}(T \ [\mathrm{K}])$", fontsize=12)
    ax.set_ylabel(r"Response $[\mathrm{DN} \cdot \mathrm{cm}^5 \cdot \mathrm{s}^{-1} \cdot \mathrm{pixel}^{-1}]$", fontsize=12)
    ax.set_title(f"AIA Temperature Response Comparison: {case['title']}", fontsize=13, fontweight="bold")
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend(ncols=2, fontsize=8.5, loc="upper right")

    # Add error metrics box
    metrics_text = f"Max Abs Diff: {max_abs_diff:.3e}\nRMSE: {rmse:.3e}\nMax Rel Diff: {max_rel_diff:.3e}"
    ax.text(0.02, 0.95, metrics_text, transform=ax.transAxes, fontsize=8.5, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='gray', alpha=0.85))

    # Precision footnote
    caption = (
        "Note: Minor sub-percent differences at peak regions are expected due to IDL's internal 32-bit single-precision\n"
        "floating point truncation compared to aiatresp's 64-bit double-precision execution."
    )
    plt.figtext(0.5, 0.01, caption, ha="center", fontsize=8, style="italic", bbox={"facecolor": "lightyellow", "alpha": 0.5, "pad": 4})

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plot_file = OUT_DIR / f"compare_{case['name']}.png"
    plt.savefig(plot_file)
    plt.close()
    return plot_file


def main():
    print("=" * 80)
    print("Generating Comparison Graphs for All AIA Calibration Versions")
    print("=" * 80)

    for case in VERSION_MATRIX:
        print(f"\nProcessing {case['title']} (Date: {case['date']})...")
        
        # 1. IDL .dat generation
        print("  - Generating IDL reference response...")
        idl_dat = generate_idl_dat(case)
        idl_raw = scipy.io.readsav(idl_dat)
        idl_tr = idl_raw['tr']  # shape: (6, 101)

        # 2. Python aiatresp response generation
        print("  - Generating aiatresp Python response...")
        max_attempts = 5
        py_resp = None
        for attempt in range(max_attempts):
            try:
                py_resp = aia_response(
                    obstime=case['date'],
                    calibration_version=case['version'],
                    logt_start=4.0,
                    logt_stop=9.0,
                    logt_step=0.05
                )
                break
            except Exception as e:
                print(f"    [Warning] Python response attempt {attempt+1}/{max_attempts} failed ({e}). Retrying in 3s...")
                time.sleep(3)

        if py_resp is None:
            raise RuntimeError(f"Failed to generate Python response for {case['name']} after {max_attempts} attempts.")

        # 3. Generate and save plot
        plot_file = generate_plot(case, idl_tr, py_resp)
        print(f"  - Plot saved to: {plot_file}")

    print("\n" + "=" * 80)
    print("All version graphs generated successfully!")
    print(f"Plots directory: {OUT_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()
