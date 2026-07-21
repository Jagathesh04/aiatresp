# aiatresp (AIA Temperature Response)

A fast, highly-optimized, Python-native package for computing Solar Dynamics Observatory (SDO) AIA temperature response functions. 

`aiatresp` is a modern Python-native package built to continue and extend the AIA temperature response calculations discontinued in recent versions of `aiapy`/`sunpy`. It provides a pure Python pipeline for computing SDO/AIA temperature response functions across all coronal channels, with numerical calculations and wavelength integration methods fully verified and validated for scientific accuracy.

## Installation

Using Conda (Recommended):
```bash
conda env create -f environment.yml
conda activate aiatresp
```

Or using pip:
```bash
pip install -e .
```

## How to Use

The package exposes a very simple single-import API. You only need to provide the observation time.

### 1. By Explicit Date
You can calculate the time-dependent degradation response by passing an explicit ISO date:
```python
from aiatresp import aia_response

response = aia_response(obstime="2017-01-01T00:00:00")
print(response.channels)
```

### 2. By Auto-Parsing FITS Directories
If you have a directory of downloaded AIA FITS files, the package can automatically parse the best co-temporal `DATE-OBS` for you! Just pass `"auto"` for the time and point it to your directory:
```python
from aiatresp import aia_response

response = aia_response(obstime="auto", fits_dir="/path/to/my/fits/directory")
```

### Using the CLI
You can also generate `.npz` (lossless Python data) or `.dat` (formatted text output) directly from the command line:

```bash
# Output text file by parsing a FITS file for the date
aia-response --fits-file /path/to/image.fits --text-output my_response.dat --output my_response.npz

# Output text file by parsing a whole directory
aia-response --fits-dir /path/to/fits/dir --text-output my_response.dat --output my_response.npz
```

## Features
- **Dynamic Response Catalog:** Automatically fetches live calibration release boundaries to select the exact calibration version (V2, V3, V4, V6, V8, V9, V10, preflight) matching your observation timestamp.
- **On-Demand Storage Optimization:** Only downloads the specific files required for the requested observation date into `~/.aia_response_native/data`. No idle datasets or storage bloat.
- **Multi-Part Parallel Downloading:** Concurrent chunk downloader for maximum bandwidth efficiency.
- **Memory Optimized:** Emissivity data is memory-shared across threads during parallel channel integrations.
- **Compatibility Helper:** Built-in `read_aia_response` helper exposing `.channels`, `.logt`, `.tr`, and `.units` attributes for downstream pipelines.
- **Open Source:** Licensed under the 100% free permissive MIT License.
