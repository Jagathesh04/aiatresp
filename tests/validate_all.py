import os
import sys
import subprocess
import numpy as np
from pathlib import Path

# Add python source to path if needed
sys.path.insert(0, str(Path(__file__).parent / "src"))

from aiatresp import aia_response
import scipy.io

TEST_CASES = [
    {"name": "v1_preflight", "version": 1, "obstime": "2010-06-01T00:00:00"},
    {"name": "v2_2011", "version": 2, "obstime": "2011-01-01T00:00:00"},
    {"name": "v3_2012", "version": 3, "obstime": "2012-01-01T00:00:00"},
    {"name": "v4_2013", "version": 4, "obstime": "2013-01-01T00:00:00"},
    {"name": "v8_2017", "version": 8, "obstime": "2017-01-01T00:00:00"},
    {"name": "v9_2019", "version": 9, "obstime": "2019-01-01T00:00:00"},
    {"name": "v10_2021", "version": 10, "obstime": "2021-01-01T00:00:00"},
    {"name": "v10_2024", "version": 10, "obstime": "2024-01-01T00:00:00"},
]

IDL_PATH = r"C:\Program Files\Exelis\IDL85\bin\bin.x86\idl.exe"
OUT_DIR = Path(__file__).parent / "verification_results"
OUT_DIR.mkdir(exist_ok=True)

def generate_idl(case):
    dat_path = OUT_DIR / f"idl_{case['name']}.dat"
    batch_path = OUT_DIR / f"run_{case['name']}.batch"
    
    date_str = case['obstime']
    idl_code = f"""
setenv,'SSW=C:\\ssw'
setenv,'SSWDB=C:\\sswdb'
@C:\\ssw\\gen\\idl\\ssw_system\\idl_startup_windows.pro
ssw_path,/aia,/chianti,/quiet
t = aia_get_response(version={case['version']}, timedepend_date='{date_str}', /temperature, /dn, /eve, /silent)
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
        raise RuntimeError(f"IDL failed for {case['name']}:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return dat_path

def generate_python(case):
    resp = aia_response(
        obstime=case['obstime'],
        calibration_version=case['version'],
        logt_start=4.0,
        logt_stop=9.0,
        logt_step=0.05
    )
    return resp

def run_verification():
    print("=" * 85)
    print(f"{'TEST CASE':<15} | {'MAX ABS DIFF':<15} | {'MAX REL DIFF':<15} | {'FIDELITY STATUS':<20}")
    print("=" * 85)
    
    summary_results = []
    
    for case in TEST_CASES:
        name = case['name']
        try:
            # 1. IDL One-by-One Generation
            idl_dat = generate_idl(case)
            idl_raw = scipy.io.readsav(idl_dat)
            idl_tr = idl_raw['tr'].T  # Transpose IDL (6, 101) to match Python (101, 6)
            
            # 2. Python One-by-One Generation
            py_resp = generate_python(case)
            py_tr = py_resp.response  # shape: (101, 6)
            
            # 3. Scientific Numerical Comparison
            abs_diff = np.abs(idl_tr - py_tr)
            max_abs_diff = np.max(abs_diff)
            
            # Relative diff where IDL response != 0
            nonzero_mask = idl_tr > 0
            if np.any(nonzero_mask):
                rel_diff = abs_diff[nonzero_mask] / idl_tr[nonzero_mask]
                max_rel_diff = np.max(rel_diff)
            else:
                max_rel_diff = 0.0
                
            # Scientific classification
            # IDL uses single-precision (float32) for internal computations (~1e-7 float precision)
            # Python uses double-precision (float64) throughout (~1e-16 float precision)
            if max_abs_diff < 1e-12:
                status = "EXACT MATCH (float64)"
            elif max_abs_diff < 1e-4:
                status = "MATCH (float32 limit)"
            else:
                status = "DISCREPANCY"
                
            print(f"{name:<15} | {max_abs_diff:<15.6e} | {max_rel_diff:<15.6e} | {status:<20}")
            summary_results.append({
                "case": name,
                "max_abs": max_abs_diff,
                "max_rel": max_rel_diff,
                "status": status
            })
        except Exception as e:
            print(f"{name:<15} | ERROR: {e}")
            
    print("=" * 85)

if __name__ == "__main__":
    run_verification()
