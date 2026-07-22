"""Integration test for AIA response generation."""

import numpy as np
import pytest
from aiatresp import aia_response


def test_aia_response_small_grid():
    resp = aia_response(
        obstime="2017-01-01T00:00:00",
        channels=(171, 193),
        logt_start=5.5,
        logt_stop=6.5,
        logt_step=0.1,
    )

    assert resp.channels == ("A171", "A193")
    assert len(resp.logt) == 11
    assert resp.response.shape == (2, 11)
    assert np.all(resp.response >= 0)
    idx_171 = 0
    max_logt_171 = resp.logt[np.argmax(resp.response[idx_171, :])]
    assert 5.7 <= max_logt_171 <= 6.1

