"""Lossless and human-readable response storage."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .models import AIAResponse


def save_npz(response: AIAResponse, path: str | Path) -> None:
    response.validate()
    np.savez_compressed(
        path,
        channels=np.asarray(response.channels, dtype="U"),
        logt=response.logt,
        response=response.response,
        units=np.asarray(response.units),
        provenance=np.asarray(json.dumps(response.provenance, sort_keys=True)),
    )


def load_npz(path: str | Path) -> AIAResponse:
    with np.load(path, allow_pickle=False) as data:
        response = AIAResponse(
            channels=tuple(data["channels"].tolist()),
            logt=data["logt"],
            response=data["response"],
            units=str(data["units"].item()),
            provenance=json.loads(str(data["provenance"].item())),
        )
    response.validate()
    return response


def save_text(response: AIAResponse, path: str | Path) -> None:
    response.validate()
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# format=aia-temperature-response-text-v1\n")
        handle.write(f"# units={response.units}\n")
        handle.write("# provenance=" + json.dumps(response.provenance, sort_keys=True) + "\n")
        handle.write("# columns=log10_temperature " + " ".join(response.channels) + "\n")
        np.savetxt(handle, np.column_stack((response.logt, response.response.T)),
                   fmt=["%.17g"] + ["%.17e"] * len(response.channels))

