"""Python-native AIA response calculation."""

from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path
from typing import Any

import numpy as np
from tqdm import tqdm

from .models import AIAResponse, ResponseRequest


def _configure_sunpy_cache() -> None:
    """Configure SunPy and Matplotlib cache directories before module import."""
    from .config import get_cache_dir
    runtime_cache = get_cache_dir() / "sunpy"
    runtime_cache.mkdir(parents=True, exist_ok=True)
    os.environ["LOCALAPPDATA"] = str(runtime_cache)
    os.environ.setdefault("SUNPY_CONFIGDIR", str(runtime_cache / "config"))
    os.environ.setdefault("SUNPY_DOWNLOADDIR", str(runtime_cache / "downloads"))
    os.environ.setdefault("MPLCONFIGDIR", str(get_cache_dir() / "matplotlib"))


# Configure cache directories before any SunPy/aiapy imports
_configure_sunpy_cache()


class AIAResponseGenerator:
    """Generate AIA temperature responses using aiapy, ChiantiPy, and NumPy."""

    def __init__(self, request: ResponseRequest):
        request.validate()
        self.request = request
        self._ensure_files()

    def _ensure_files(self):
        from .downloader import download_file
        from .config import get_cache_dir
        from .catalog import resolve_genx_filenames
        
        cache_dir = get_cache_dir()
        eff_version = self.request.effective_calibration_version()
        emiss_name, inst_name = resolve_genx_filenames(eff_version)

        if self.request.emissivity_file is None:
            dest = cache_dir / emiss_name
            url = f"https://hesperia.gsfc.nasa.gov/ssw/sdo/aia/response/{emiss_name}"
            download_file(url, dest)
            self.emissivity_file = dest
        else:
            self.emissivity_file = self.request.emissivity_file
            
        if self.request.instrument_file is None:
            dest = cache_dir / inst_name
            url = f"https://hesperia.gsfc.nasa.gov/ssw/sdo/aia/response/{inst_name}"
            download_file(url, dest)
            self.instrument_file = dest
        else:
            self.instrument_file = self.request.instrument_file

    @staticmethod
    def _versions() -> dict[str, str]:
        return {name: importlib.metadata.version(name) for name in ("numpy", "astropy", "aiapy", "scipy")}

    def generate(self) -> AIAResponse:
        """Generate the full response grid without any IDL dependency."""
        from sunpy.io.special.genx import read_genx
        import astropy.units as u
        from aiapy.response import Channel
        from astropy.table import Table
        from astropy.time import Time
        
        print(f"Loading large IDL GENX emissivity file (this may take 1-2 minutes)...")
        emiss_data = read_genx(str(self.emissivity_file))
        
        emiss_wave = np.asarray(emiss_data['TOTAL']['WAVE'], dtype=np.float64)
        emiss_logt = np.asarray(emiss_data['TOTAL']['LOGTE'], dtype=np.float64)
        emiss_spectrum = np.asarray(emiss_data['TOTAL']['EMISSIVITY'], dtype=np.float64)
        
        # Handle shape differences if read_genx returns transposed
        if emiss_spectrum.shape == (emiss_wave.size, emiss_logt.size):
            emiss_spectrum = emiss_spectrum.T
            
        wavestep = emiss_wave[1] - emiss_wave[0]
        
        native_output = np.empty((emiss_logt.size, len(self.request.channels)), dtype=np.float64)
        
        def _fetch_correction_table():
            def _try_get():
                for module_path in (
                    "aiapy.calibrate.utils",
                    "aiapy.calibrate.util",
                    "aiapy.calibrate",
                    "aiapy.calibrate.degradation",
                ):
                    try:
                        mod = __import__(module_path, fromlist=["get_correction_table"])
                        func = getattr(mod, "get_correction_table", None)
                        if func is not None:
                            try:
                                return func(source="SSW")
                            except TypeError:
                                return func()
                    except (ImportError, AttributeError, ModuleNotFoundError):
                        continue
                return None

            try:
                tbl = _try_get()
                if tbl is not None:
                    return tbl
            except Exception:
                try:
                    from astropy.utils.data import clear_download_cache
                    clear_download_cache()
                except Exception:
                    pass
                tbl = _try_get()
                if tbl is not None:
                    return tbl

            raise RuntimeError("Could not locate or fetch get_correction_table in aiapy.calibrate")



        def process_channel(idx: int, channel_angstrom: int):
            c = Channel(channel_angstrom * u.angstrom, instrument_file=str(self.instrument_file))
            if self.request.correction_table is not None:
                correction_table = Table.read(self.request.correction_table)
            else:
                correction_table = _fetch_correction_table()
            
            obstime_obj = None
            if self.request.observation_time:
                obs_t_str = str(self.request.observation_time).replace("+00:00", "")
                if obs_t_str.endswith("Z"):
                    obs_t_str = obs_t_str[:-1]
                obstime_obj = Time(obs_t_str)

            response = c.wavelength_response(
                obstime=obstime_obj,
                include_eve_correction=self.request.include_eve_correction,
                include_crosstalk=self.request.include_crosstalk,
                correction_table=correction_table,
            )


            native_wavelength = c.wavelength.to_value(u.angstrom)
            values = np.asarray(response.value, dtype=np.float64)
            
            iresponse = np.interp(emiss_wave, native_wavelength, values, left=0.0, right=0.0)
            iresponse = np.clip(iresponse, 0, None)
            
            channel_resp = np.sum(iresponse[np.newaxis, :] * emiss_spectrum, axis=1)
            return idx, channel_resp * self.request.pixel_solid_angle_sr * wavestep

        from concurrent.futures import ThreadPoolExecutor, as_completed

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_channel, i, ch) for i, ch in enumerate(self.request.channels)]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Calculating Channels", unit="channel"):
                idx, result = future.result()
                native_output[:, idx] = result

        user_temperature = self.request.temperatures()
        user_logt = np.log10(user_temperature)
        output = np.empty((len(self.request.channels), user_logt.size), dtype=np.float64)
        
        for index in range(len(self.request.channels)):
            output[index, :] = np.interp(user_logt, emiss_logt, native_output[:, index], left=0.0, right=0.0)

            
        provenance: dict[str, Any] = self.request.provenance()
        provenance.update({
            "engine": "aiapy + scipy + NumPy",
            "package_versions": self._versions(),
            "integration": "Exact IDL match: interpolation onto CHIANTI wave grid and direct summation",
            "spectrum": "Pre-computed CHIANTI emissivity from IDL GENX file",
            "observation_time": self.request.observation_time,
        })
        
        result = AIAResponse(
            channels=tuple(f"A{channel}" for channel in self.request.channels),
            logt=user_logt,
            response=output,
            units="DN cm^5 s^-1 pix^-1",
            provenance=provenance,
        )
        result.validate()
        return result
