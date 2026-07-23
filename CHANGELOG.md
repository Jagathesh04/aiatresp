# Changelog

All notable changes to `aiatresp` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-07-24

### Added
- **Comprehensive 13-Release Verification Matrix**: Added full side-by-side comparison plots, error matrices, and numerical validation across all 13 official SDO/AIA calibration releases (preflight, V2 to V10c) in `COMPARISON.md` and `docs/version_plots/`.
- **Author Attribution**: Added co-author Aparna G R to `pyproject.toml`, `README.md`, and package metadata.
- **Visual README Badges**: Added GitHub circular profile avatar bubbles and dynamic contributor metrics.

### Changed
- **Network Resilience & Offline Fallback**: Implemented automatic cache persistence when using offline defaults, multi-mirror retry loops, and graceful network outage handling in `downloader.py` and `catalog.py`.
- **Modern Conda-Forge Recipe**: Updated Conda-Forge recipe to Rattler `v1` schema (`schema_version: 1`).

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
