# aiatresp (AIA Temperature Response)

A fast, highly-optimized, Python-native package for computing Solar Dynamics Observatory (SDO) AIA temperature response functions. 

`aiatresp` perfectly mimics the output of the legacy IDL SolarSoft `aia_get_response` routine natively in Python. It removes all IDL dependencies while mathematically reproducing the identical integrations (interpolation onto the CHIANTI wavelength grid and direct summation) down to decimal precision.

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
You can also generate `.npz` (lossless Python data) or `.dat` (IDL-style text output) directly from the command line:

```bash
# Output IDL-style .dat file by parsing a FITS file for the date
aia-response --fits-file /path/to/image.fits --text-output my_response.dat --output my_response.npz

# Output IDL-style .dat file by parsing a whole directory
aia-response --fits-dir /path/to/fits/dir --text-output my_response.dat --output my_response.npz
```

## Features
- **16-Part Parallel IDM-style Downloading:** Extremely fast setup. The massive 789 MB CHIANTI emissivity matrices are downloaded in 16 simultaneous chunks concurrently to maximize your bandwidth.
- **Memory Optimized:** Emissivity data is memory-shared across threads during the parallel channel integrations, perfectly scaling within RAM limits.
- **Cache Management:** All files are cached centrally in `~/.aia_response_native/data`. You can clear this cache at any time by running `aia-response --clear-cache`.
