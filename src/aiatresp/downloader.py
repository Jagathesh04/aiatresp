import os
import shutil
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
import random
from tqdm import tqdm


def urlopen_with_retry(req, max_retries=5, timeout=60):
    for attempt in range(max_retries):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(1 + attempt + random.random() * 2)


def download_chunk(url: str, start: int, end: int, part_num: int, temp_dir: Path) -> Path:
    chunk_path = temp_dir / f"chunk_{part_num}.part"
    
    req = urllib.request.Request(url)
    req.add_header('Range', f'bytes={start}-{end}')
    with urlopen_with_retry(req) as response, open(chunk_path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    
    return chunk_path


def download_file(url: str, dest_path: Path, max_parts: int = 16) -> None:
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Try primary URL, then secondary mirror URL fallback if available
    urls_to_try = [url]
    if "hesperia.gsfc.nasa.gov" in url:
        urls_to_try.append(url.replace("hesperia.gsfc.nasa.gov", "soho.nascom.nasa.gov"))
    elif "soho.nascom.nasa.gov" in url:
        urls_to_try.append(url.replace("soho.nascom.nasa.gov", "hesperia.gsfc.nasa.gov"))

    last_error = None
    for target_url in urls_to_try:
        for attempt in range(3):
            try:
                return _download_from_url(target_url, dest_path, max_parts)
            except Exception as e:
                last_error = e
                print(f"Warning: Download from {target_url} failed (attempt {attempt + 1}/3: {e}). Retrying...")
                time.sleep(1 + attempt)
    
    raise RuntimeError(f"Failed to download {dest_path.name} from all mirrors: {last_error}")



def _download_from_url(url: str, dest_path: Path, max_parts: int = 16) -> None:
    req = urllib.request.Request(url, method='HEAD')
    total_size = None
    try:
        with urlopen_with_retry(req) as response:
            cl = response.headers.get('Content-Length')
            if cl:
                total_size = int(cl)
    except Exception:
        pass

    if dest_path.exists():
        if total_size is None or dest_path.stat().st_size == total_size:
            return
        else:
            print(f"Incomplete cached file detected for {dest_path.name} (size mismatch). Re-downloading...")
            dest_path.unlink()

    if not total_size:
        print(f"Downloading {dest_path.name} in 1 part (no Content-Length)...")
        tmp_target = dest_path.with_suffix(".tmp_download")
        with urlopen_with_retry(urllib.request.Request(url)) as response, open(tmp_target, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        tmp_target.replace(dest_path)
        return

    num_parts = min(max_parts, max(1, total_size // (10 * 1024 * 1024)))
    print(f"Downloading {dest_path.name} in {num_parts} parts...")
    
    chunk_size = total_size // num_parts
    
    temp_dir = dest_path.parent / f".tmp_{dest_path.name}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    ranges = []
    for i in range(num_parts):
        start = i * chunk_size
        end = start + chunk_size - 1 if i < num_parts - 1 else total_size - 1
        ranges.append((start, end))

    downloaded_chunks = [None] * num_parts
    
    with ThreadPoolExecutor(max_workers=num_parts) as executor:
        future_to_part = {
            executor.submit(download_chunk, url, r[0], r[1], i, temp_dir): i
            for i, r in enumerate(ranges)
        }
        
        with tqdm(total=total_size, unit='iB', unit_scale=True, desc=dest_path.name) as pbar:
            for future in as_completed(future_to_part):
                part_num = future_to_part[future]
                chunk_path = future.result()
                downloaded_chunks[part_num] = chunk_path
                pbar.update(ranges[part_num][1] - ranges[part_num][0] + 1)
                
    tmp_target = dest_path.with_suffix(".tmp_download")
    with open(tmp_target, 'wb') as outfile:
        for chunk_path in downloaded_chunks:
            if chunk_path and chunk_path.exists():
                with open(chunk_path, 'rb') as infile:
                    shutil.copyfileobj(infile, outfile)
                chunk_path.unlink()

    tmp_target.replace(dest_path)
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
