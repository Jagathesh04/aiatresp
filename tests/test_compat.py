"""Tests for data models, storage (npz/text), and scipy readsav compatibility layer."""

import tempfile
from pathlib import Path
import numpy as np
import pytest

from aiatresp import ResponseRequest, AIAResponse
from aiatresp.storage import save_npz, load_npz, save_text
from aiatresp.compat import read_aia_response


def test_response_request_grid():
    req = ResponseRequest(logt_start=4.0, logt_stop=9.0, logt_step=0.05)
    temps = req.temperatures()
    logt = np.log10(temps)
    assert len(logt) == 101
    assert np.isclose(logt[0], 4.0)
    assert np.isclose(logt[-1], 9.0)


def test_response_request_validation():
    with pytest.raises(ValueError, match="Grid steps must be positive"):
        ResponseRequest(logt_step=-0.1, observation_time="2019-01-01T00:00:00").validate()

    with pytest.raises(ValueError, match="Grid stop values must be greater than start values"):
        ResponseRequest(logt_start=8.0, logt_stop=7.0, observation_time="2019-01-01T00:00:00").validate()


def test_storage_roundtrip():
    channels = ("A94", "A131", "A171")
    logt = np.linspace(4.0, 9.0, 50)
    response_data = np.random.rand(3, 50)

    units = "DN cm^5 s^-1 pix^-1"
    provenance = {"engine": "test", "version": "1.0"}

    resp = AIAResponse(
        channels=channels,
        logt=logt,
        response=response_data,
        units=units,
        provenance=provenance,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        npz_path = Path(tmpdir) / "test.npz"
        dat_path = Path(tmpdir) / "test.dat"

        # Test NPZ save and load
        save_npz(resp, npz_path)
        loaded = load_npz(npz_path)

        assert loaded.channels == channels
        assert np.allclose(loaded.logt, logt)
        assert np.allclose(loaded.response, response_data)
        assert loaded.units == units
        assert loaded.provenance["engine"] == "test"

        # Test compat read_aia_response
        compat_obj = read_aia_response(npz_path)
        assert compat_obj.channels == channels
        assert np.allclose(compat_obj.logt, logt)
        assert np.allclose(compat_obj.tr, response_data)
        assert compat_obj.units == units

        # Test text output
        save_text(resp, dat_path)
        assert dat_path.exists()
        lines = dat_path.read_text(encoding="utf-8").splitlines()
        assert lines[0].startswith("# format=")
        assert lines[1].startswith("# units=")


def test_version_prefix_mapping():
    from aiatresp.catalog import resolve_genx_filenames

    emiss, inst = resolve_genx_filenames(10)
    assert emiss == "aia_V9_fullemiss.genx"
    assert inst == "aia_V9_all_fullinst.genx"

    emiss3, inst3 = resolve_genx_filenames(3)
    assert emiss3 == "aia_V3_fullemiss.genx"
    assert inst3 == "aia_V3_all_fullinst.genx"

    with pytest.raises(ValueError, match="Unsupported calibration_version"):
        resolve_genx_filenames(99)

    with pytest.raises(ValueError, match="Invalid calibration_version"):
        resolve_genx_filenames("invalid_version")


def test_infer_calibration_version_from_date():
    from aiatresp.models import infer_calibration_version_from_date, ResponseRequest

    # Dynamic catalog matching SSW response table publication timestamps:
    assert infer_calibration_version_from_date("2010-04-30T23:59:59") == "preflight"
    assert infer_calibration_version_from_date("2010-05-01T00:00:00") == "preflight"
    assert infer_calibration_version_from_date("2011-11-29T00:00:00") == 2
    assert infer_calibration_version_from_date("2012-09-27T00:00:00") == 3
    assert infer_calibration_version_from_date("2013-01-10T00:00:00") == 4
    assert infer_calibration_version_from_date("2014-05-10T00:00:00") == 6
    assert infer_calibration_version_from_date("2017-12-01T00:00:00") == 8
    assert infer_calibration_version_from_date("2020-07-07T00:00:00") == 9
    assert infer_calibration_version_from_date("2020-12-01T00:00:00") == 10


    # Auto inference when calibration_version is None
    req_date = ResponseRequest(observation_time="2012-10-01T00:00:00")
    assert req_date.effective_calibration_version() == 3

    # Explicit override takes precedence
    req_override = ResponseRequest(observation_time="2012-05-01T00:00:00", calibration_version=9)
    assert req_override.effective_calibration_version() == 9

    # Error raised when neither date nor calibration_version is provided (no silent fallback to 10)
    req_no_info = ResponseRequest()
    with pytest.raises(ValueError, match="Cannot determine AIA calibration version"):
        req_no_info.effective_calibration_version()


def test_dynamic_catalog_resolution():
    from aiatresp.catalog import get_ssw_catalog, resolve_genx_filenames

    catalog = get_ssw_catalog()
    assert isinstance(catalog, list)
    assert len(catalog) > 0

    emiss, inst = resolve_genx_filenames(3)
    assert emiss == "aia_V3_fullemiss.genx"
    assert inst == "aia_V3_all_fullinst.genx"

    emiss_pre, inst_pre = resolve_genx_filenames("preflight")
    assert emiss_pre == "aia_preflight_fullemiss.genx"
    assert inst_pre == "aia_preflight_all_fullinst.genx"
