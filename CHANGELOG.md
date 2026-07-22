# Changelog

All notable changes to `aiatresp` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-22

### Added
- **Pure Python Core:** Complete native replacement for SolarSoft's `aia_get_response` routine without IDL runtime dependencies.
- **Support for Calibration Versions:** Supports all AIA calibration versions (Version 1 / Pre-flight through Version 10).
- **Time-Dependent Degradation:** Time-dependent instrument degradation corrections and EVE normalization.
- **Platform Cache Management:** Cross-platform cache directory using `platformdirs`.
- **Diagnostic CLI:** Added `aia-response --info` subcommand to display cache status, version information, and downloaded data files.
- **16-Part Parallel Downloader:** Multi-threaded chunk downloader with exponential backoff and jitter for reliable data retrieval.
- **Scientific Verification Suite:** Added `examples/compare_with_ssw.py` computing Max Relative Error and RMSE against SolarSoft IDL baseline outputs.
- **Consolidated Test Suite:** `tests/test_all.py` pytest suite with zero hardcoded username paths.
- **GitHub Actions CI:** `.github/workflows/ci.yml` matrix testing across Python 3.10, 3.11, and 3.12.
