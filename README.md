# aiatresp

`aiatresp` is a pure Python replacement for SolarSoft's `aia_get_response()` routine.

It computes the SDO/AIA temperature response functions for all coronal channels without requiring IDL or SolarSoft while remaining numerically consistent with the official AIA calibration files.

## Workflow Translation

```text
IDL (SolarSoft)
-------------------------------------------------------------
aia_get_response, '2014-03-29', channels, logt, tr, /chianti

                     ↓

Python (aiatresp)
-------------------------------------------------------------
from aiatresp import aia_response

response = aia_response(obstime="2014-03-29")
channels = response.channels
logt = response.logt
tr = response.response  # Array shape: (6, 101) -> (channels, temperature)
```

## Features

- **Pure Python Replacement for `aia_get_response`**: Computes time-dependent AIA temperature responses without any IDL or SolarSoft installation.
- **Dynamic SSW Catalog Tracking**: Automatically fetches live SolarSoft calibration indices (`https://hesperia.gsfc.nasa.gov/ssw/sdo/aia/response/`) to auto-discover active calibration versions (V1–V10, preflight, and future releases like V11) without hardcoded lookup tables.
- **Time-Dependent Degradation & Crosstalk**: Full support for time-dependent EVE degradation corrections and channel crosstalk.
- **On-Demand Storage Discipline**: Downloads only the specific single calibration version files needed into cross-platform cache locations (`platformdirs`).
- **Parallel Downloader & Calculator**: Multi-part parallel chunk downloader for maximum speed and vectorized NumPy integration.
- **`scipy.io.readsav` Drop-in Compatibility**: Includes `read_aia_response` helper exposing `.channels`, `.logt`, `.tr`, and `.units`.

## Installation

Clone the repository and enter the project directory:
```bash
git clone https://github.com/Jagathesh04/aiatresp.git && cd aiatresp
```

Install `aiatresp` directly into your active environment (Conda or `.venv`):
```bash
pip install .
```

For editable/development installation:
```bash
pip install -e .
```

## Usage

### 1. By Observation Date
You can calculate temperature response functions by passing an ISO date string:
```python
from aiatresp import aia_response

response = aia_response(obstime="2017-01-01T00:00:00")
print("Channels:", response.channels)
print("Response shape:", response.response.shape)  # (6, 101) -> (channels, temperature)
```

### 2. By Auto-Parsing FITS Directories
Pass `obstime="auto"` and supply the directory containing AIA FITS files:
```python
from aiatresp import aia_response

response = aia_response(obstime="auto", fits_dir="/path/to/my/fits/directory")
```


### 3. Command-Line Interface (CLI)

```bash
# Output text and .npz response files from observation time
aia-response --observation-time "2019-01-01T00:00:00" --output resp.npz --text-output resp.dat

# Display environment & cache diagnostics
aia-response info

# Clear cached calibration files
aia-response --clear-cache
```

## Scientific Validation

Full side-by-side comparison plots and numerical validation against SolarSoft IDL `aia_get_response` across all calibration versions (V1 to V10) are available in [COMPARISON.md](COMPARISON.md).

## Verification & Testing

Run the automated test suite with `pytest`:
```bash
pytest -v
```

Run the scientific verification script against SolarSoft reference standards:
```bash
python examples/compare_with_ssw.py
```

## License


Distributed under the terms of the [MIT License](LICENSE).
