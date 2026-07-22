"""Tests for FITS directory observation time parsing."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
import pytest
from astropy.io import fits

from aiatresp.fits import parse_date_from_directory


def test_fits_directory_parsing():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        channels = [94, 131, 171, 193, 211, 335]
        target_iso = "2020-05-15T12:00:00.000"

        for ch in channels:
            hdu = fits.PrimaryHDU()
            hdu.header["WAVELNTH"] = ch
            hdu.header["DATE-OBS"] = target_iso
            hdul = fits.HDUList([hdu])
            hdul.writeto(tmp_path / f"aia_0{ch}.fits")

        best_dt = parse_date_from_directory(tmp_path)
        assert isinstance(best_dt, datetime)
        assert best_dt.year == 2020
        assert best_dt.month == 5
        assert best_dt.day == 15
        assert best_dt.hour == 12


def test_fits_directory_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(ValueError, match="No valid AIA FITS files found"):
            parse_date_from_directory(tmpdir)
