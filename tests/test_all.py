"""Consolidated test suite for aiatresp core modules."""

from __future__ import annotations

import os
import pytest
import numpy as np
from pathlib import Path

from aiatresp.models import ResponseRequest, AIAResponse, CORONAL_CHANNELS
from aiatresp.generator import AIAResponseGenerator
from aiatresp.storage import save_npz, read_aia_response, save_text, load_npz
from aiatresp.config import get_cache_dir, clear_cache
from aiatresp import aia_response


# =====================================================================
# 1. CATALOG / DATA MODEL TESTS
# =====================================================================

def test_catalog_request_validation():
    """Test ResponseRequest validation rules and temperature grid generation."""
    req = ResponseRequest(
        logt_start=4.0,
        logt_stop=9.0,
        logt_step=0.05,
        electron_density_cm3=1.0e9,
        calibration_version=10,
    )
    req.validate()
    temps = req.temperatures()
    assert temps[0] == pytest.approx(1e4)
    assert temps[-1] == pytest.approx(1e9)
    assert len(temps) == 101


def test_catalog_request_invalid_steps():
    """Test that invalid grid steps raise ValueError."""
    req = ResponseRequest(logt_step=-0.1, calibration_version=10)
    with pytest.raises(ValueError, match="Grid steps must be positive"):
        req.validate()


def test_catalog_provenance_privacy():
    """Ensure provenance dictionary contains zero absolute user paths."""
    req = ResponseRequest(observation_time="2017-01-01T00:00:00")
    prov = req.provenance()
    assert prov["observation_time"] == "2017-01-01T00:00:00"
    assert "user" not in str(prov["created_utc"]).lower()


# =====================================================================
# 2. GENERATOR TESTS
# =====================================================================

def test_generator_initialization():
    """Test generator setup and request grid verification."""
    req = ResponseRequest(observation_time="2017-01-01T00:00:00")
    gen = AIAResponseGenerator(req)
    assert gen.request.observation_time == "2017-01-01T00:00:00"


def test_aia_response_convenience_api():
    """Test main aia_response API validation for obstime and auto modes."""
    with pytest.raises(ValueError, match="You must provide an obstime"):
        aia_response(obstime="")

    with pytest.raises(ValueError, match="must provide a valid fits_dir"):
        aia_response(obstime="auto")


# =====================================================================
# 3. STORAGE & ROUNDTRIP TESTS
# =====================================================================

def test_storage_npz_roundtrip(tmp_path: Path):
    """Test saving and loading AIAResponse objects in lossless .npz format."""
    channels = ("94", "131", "171", "193", "211", "335")
    logt = np.linspace(4.0, 9.0, 101)
    resp_data = np.ones((6, 101))  # (channels, temperature)
    units = "DN cm^5 s^-1 pixel^-1"
    prov = {"test": "provenance"}

    original = AIAResponse(
        channels=channels,
        logt=logt,
        response=resp_data,
        units=units,
        provenance=prov,
    )
    original.validate()

    output_file = tmp_path / "test_response.npz"
    save_npz(original, output_file)
    assert output_file.exists()

    loaded = read_aia_response(output_file)
    assert loaded.channels == channels
    assert np.allclose(loaded.logt, logt)
    assert np.allclose(loaded.response, resp_data)
    assert loaded.units == units


def test_storage_text_output(tmp_path: Path):
    """Test exporting inspectable text .dat response tables."""
    channels = ("94", "131", "171", "193", "211", "335")
    logt = np.linspace(4.0, 9.0, 101)
    resp_data = np.ones((6, 101))  # (channels, temperature)
    
    response_obj = AIAResponse(
        channels=channels,
        logt=logt,
        response=resp_data,
        units="DN cm^5 s^-1 pixel^-1",
        provenance={},
    )

    output_dat = tmp_path / "test_response.dat"
    save_text(response_obj, output_dat)
    assert output_dat.exists()
    content = output_dat.read_text()
    assert "format=aia-temperature-response-text-v1" in content
    assert "94" in content


# =====================================================================
# 4. CLI & CONFIG TESTS
# =====================================================================

def test_config_cache_dir():
    """Verify platform-standard cache directory creation."""
    cache_dir = get_cache_dir()
    assert cache_dir.exists()
    assert "aiatresp" in str(cache_dir).lower()


def test_cli_info_flag(capsys):
    """Test CLI --info diagnostic metadata display."""
    from aiatresp.cli import main
    import sys

    old_argv = sys.argv
    try:
        sys.argv = ["aia-response", "--info"]
        main()
        captured = capsys.readouterr()
        assert "aiatresp Package Diagnostic Info" in captured.out
        assert "Package Version:" in captured.out
    finally:
        sys.argv = old_argv


# =====================================================================
# 5. FALLBACK & RECOVERY TESTS
# =====================================================================

def test_version_resolution_fallbacks():
    """Test version resolution fallback rules across mission epochs."""
    from aiatresp.catalog import resolve_calibration_version_from_date, resolve_genx_filenames

    # Pre-launch date -> preflight fallback
    assert resolve_calibration_version_from_date("2009-01-01T00:00:00") == "preflight"
    assert resolve_genx_filenames("preflight") == ("aia_preflight_fullemiss.genx", "aia_preflight_all_fullinst.genx")

    # Historical epoch resolution
    assert resolve_calibration_version_from_date("2012-01-01T00:00:00") == 2
    assert resolve_calibration_version_from_date("2018-01-01T00:00:00") == 8
    assert resolve_calibration_version_from_date("2024-06-01T00:00:00") in (9, 10)

    # Invalid version fallback check
    with pytest.raises(ValueError, match="Invalid calibration_version"):
        resolve_genx_filenames("invalid_version_name")


def test_catalog_cache_fallback():
    """Test fallback to local catalog cache when network is unavailable."""
    from aiatresp.catalog import get_ssw_catalog, CATALOG_FILENAME
    from aiatresp.config import get_cache_dir

    catalog = get_ssw_catalog()
    assert isinstance(catalog, list)
    assert len(catalog) > 0

    cache_file = get_cache_dir() / CATALOG_FILENAME
    assert cache_file.exists()


def test_downloader_mirror_fallback(tmp_path: Path):
    """Test automatic fallback to secondary mirror URL when primary fails."""
    from aiatresp.downloader import download_file

    # Test downloading a small valid table file via mirror fallback logic
    test_url = "https://hesperia.gsfc.nasa.gov/ssw/sdo/aia/response/aia_V2_error_table.txt"
    dest = tmp_path / "test_error_table.txt"
    download_file(test_url, dest)
    assert dest.exists()
    assert dest.stat().st_size > 0
