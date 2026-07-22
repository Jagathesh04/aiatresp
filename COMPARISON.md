# Side by side comparison with SolarSoft IDL

This document presents the side-by-side scientific verification and numerical comparison between SolarSoft IDL `aia_get_response` and `aiatresp` (Python) across all official SDO/AIA calibration versions.

---

## 1. Version 1 (Pre-flight)
![Version 1 Comparison](docs/version_plots/compare_v1_preflight.png)

## 2. Version 2 (Epoch 2011)
![Version 2 Comparison](docs/version_plots/compare_v2_2011.png)

## 3. Version 3 (Epoch 2012)
![Version 3 Comparison](docs/version_plots/compare_v3_2012.png)

## 4. Version 4 (Epoch 2013)
![Version 4 Comparison](docs/version_plots/compare_v4_2013.png)

## 5. Version 8 (Epoch 2017)
![Version 8 Comparison](docs/version_plots/compare_v8_2017.png)

## 6. Version 9 (Epoch 2019)
![Version 9 Comparison](docs/version_plots/compare_v9_2019.png)

## 7. Version 10 (Epoch 2024 - Latest)
![Version 10 Comparison](docs/version_plots/compare_v10_2024.png)

---

### Precision Note
*Sub-percent differences at curve peaks are expected due to IDL's internal 32-bit single-precision (`float32`) floating-point truncation compared to `aiatresp`'s native 64-bit double-precision (`float64`) execution.*
