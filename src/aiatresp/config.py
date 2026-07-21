import os
import shutil
from pathlib import Path


def get_cache_dir() -> Path:
    """Get the default cache directory for downloaded response files."""
    env_dir = os.environ.get("AIA_RESPONSE_CACHE_DIR")
    if env_dir:
        cache_dir = Path(env_dir)
    else:
        cache_dir = Path.home() / ".aia_response_native" / "data"
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def clear_cache() -> None:
    """Clear all downloaded files in the cache directory."""
    cache_dir = get_cache_dir()
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print(f"Cache cleared at {cache_dir}")
    cache_dir.mkdir(parents=True, exist_ok=True)
