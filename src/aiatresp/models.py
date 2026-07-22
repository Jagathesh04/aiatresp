"""Versioned data models for response calculations."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


CORONAL_CHANNELS = (94, 131, 171, 193, 211, 335)


def infer_calibration_version_from_date(obstime: str | datetime) -> int | str:
    """Dynamically infer the exact AIA calibration version (e.g., 2, 3, 4, 6, 8, 9, 10, or preflight)
    by matching the observation timestamp against the official SSW response table catalog.
    """
    from .catalog import resolve_calibration_version_from_date
    return resolve_calibration_version_from_date(obstime)


@dataclass(frozen=True)
class ResponseRequest:
    """All scientific and calibration inputs required for a reproducible run."""

    emissivity_file: Path | None = None
    instrument_file: Path | None = None
    correction_table: Path | None = None
    channels: tuple[int, ...] = CORONAL_CHANNELS
    logt_start: float = 4.0
    logt_stop: float = 9.0
    logt_step: float = 0.05
    wavelength_start: float = 1.0
    wavelength_stop: float = 2000.0
    wavelength_step: float = 0.1
    electron_density_cm3: float = 1.0e9
    abundance: str = "sun_coronal_2021_chianti"
    ionization_equilibrium: str = "chianti"
    minimum_abundance: float = 1.0e-6
    calibration_version: int | str | None = None
    observation_time: str | None = None
    include_eve_correction: bool = True
    include_crosstalk: bool = True
    pixel_solid_angle_sr: float = 8.4e-12

    def effective_calibration_version(self) -> int | str:
        if self.calibration_version is not None:
            return self.calibration_version
        if self.observation_time is not None:
            return infer_calibration_version_from_date(self.observation_time)
        raise ValueError(
            "Cannot determine AIA calibration version: Neither 'observation_time' "
            "(or FITS header date) nor explicit 'calibration_version' was provided. "
            "Please specify an observation date or calibration version."
        )

    def temperatures(self) -> np.ndarray:
        count = round((self.logt_stop - self.logt_start) / self.logt_step)
        return np.power(10.0, self.logt_start + np.arange(count + 1) * self.logt_step)

    @classmethod
    def from_fits_directory(cls, data_dir: str | Path, **kwargs) -> ResponseRequest:
        """Create a ResponseRequest by automatically parsing the best observation time from a FITS directory."""
        from .fits import parse_date_from_directory
        best_time = parse_date_from_directory(data_dir)
        return cls(observation_time=best_time.isoformat(), **kwargs)

    def wavelengths(self) -> np.ndarray:
        count = round((self.wavelength_stop - self.wavelength_start) / self.wavelength_step)
        return self.wavelength_start + np.arange(count + 1) * self.wavelength_step

    def validate(self) -> None:
        _ = self.effective_calibration_version()
        if self.logt_step <= 0 or self.wavelength_step <= 0:
            raise ValueError("Grid steps must be positive")
        if self.logt_stop <= self.logt_start or self.wavelength_stop <= self.wavelength_start:
            raise ValueError("Grid stop values must be greater than start values")
        if self.electron_density_cm3 <= 0 or self.pixel_solid_angle_sr <= 0 or self.minimum_abundance <= 0:
            raise ValueError("Density, pixel solid angle, and minimum abundance must be positive")
        if self.emissivity_file is not None and not self.emissivity_file.exists():
            raise FileNotFoundError(self.emissivity_file)
        if self.instrument_file is not None and not self.instrument_file.exists():
            raise FileNotFoundError(self.instrument_file)
        if self.correction_table is not None and not self.correction_table.exists():
            raise FileNotFoundError(self.correction_table)

    def provenance(self) -> dict[str, Any]:
        value = asdict(self)
        for key in ("emissivity_file", "instrument_file", "correction_table"):
            value[key] = None if value[key] is None else str(value[key])
        value["created_utc"] = datetime.now(timezone.utc).isoformat()
        return value


@dataclass(frozen=True)
class AIAResponse:
    """Temperature response values plus complete calculation provenance."""

    channels: tuple[str, ...]
    logt: np.ndarray
    response: np.ndarray
    units: str
    provenance: dict[str, Any]

    def validate(self) -> None:
        if self.response.shape != (len(self.channels), self.logt.size):
            raise ValueError("Response dimensions do not match the channels and temperature grid (channels, temperature)")
        if not np.isfinite(self.response).all():
            raise ValueError("Response contains non-finite values")

