"""Drop-in replacement for ``scipy.io.readsav`` for native AIA response files."""

from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path

from .storage import load_npz


def read_aia_response(path: str | Path) -> SimpleNamespace:
    """Load native output with the attribute layout used by ``scipy.io.readsav``.

    Replace only this line in an existing pipeline::

        old_data = scipy.io.readsav(old_filepath)

    with::

        old_data = read_aia_response(new_filepath)
    """
    response = load_npz(path)
    return SimpleNamespace(
        channels=response.channels,
        logt=response.logt,
        tr=response.response,
        units=response.units,
    )
