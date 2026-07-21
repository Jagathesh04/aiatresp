from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from .models import ResponseRequest, AIAResponse
from .generator import AIAResponseGenerator
from .config import clear_cache


def aia_response(
    obstime: str,
    fits_dir: Optional[Union[str, Path]] = None,
    **kwargs
) -> AIAResponse:
    """Convenience function to generate AIA temperature responses.
    
    Parameters
    ----------
    obstime : str
        ISO formatted date string (e.g., '2019-01-01T00:00:00') OR 'auto'. 
        If 'auto', you must provide `fits_dir`.
    fits_dir : str or Path, optional
        Directory containing 6 AIA FITS channels to parse the date from.
    **kwargs :
        Additional arguments passed to `ResponseRequest` (e.g., channels).
        
    Returns
    -------
    AIAResponse
        The generated response object containing the logt array and response grid.
    """
    if not obstime:
        raise ValueError("You must provide an obstime (e.g., '2019-01-01T00:00:00') or set obstime='auto' and provide fits_dir.")
        
    if str(obstime).lower() == "auto":
        if not fits_dir:
            raise ValueError("When obstime='auto', you must provide a valid fits_dir to parse the date from.")
        req = ResponseRequest.from_fits_directory(fits_dir, **kwargs)
    else:
        req = ResponseRequest(observation_time=obstime, **kwargs)
        
    return AIAResponseGenerator(req).generate()


__all__ = [
    "aia_response",
    "clear_cache",
    "ResponseRequest",
    "AIAResponse",
    "AIAResponseGenerator",
]
