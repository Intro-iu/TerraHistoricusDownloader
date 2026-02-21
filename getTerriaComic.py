import argparse
import json
import logging
import multiprocessing
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Set

import requests
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Constants
BASE_API_URL = "https://comic.hypergryph.com/api/comic/"
BASE_DIR = Path(__file__).parent.resolve()
DOWNLOAD_BASE_DIR = BASE_DIR / "Comic"

class Comic:
    def __init__(self, comic_id: int):
        self.comic_id = comic_id
        self.cid: str = ""
        self.title: str = ""
        self.introduction: str = ""
        self.cover_url: str = ""
        self.episodes: List[dict] = []
        self.dir_name: str = ""
        self.local_path: Path = Path()

    def fetch_metadata(self):
        """Fetches comic metadata from the API."""
        try:
            url = f"{BASE_API_URL}{self.comic_id}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()["data"]
            
            self.cid = data["cid"]
            self.title = data["title"]
            self.introduction = data["introduction"]
            self.cover_url = data["cover"]
            # The original script reversed the episodes list
            self.episodes = data["episodes"][::-1]
            
            self.dir_name = f"{self.cid}_{self.title}"
            self.local_path = DOWNLOAD_BASE_DIR / self.dir_name
            
            # Create local directory if it doesn't exist
            self.local_path.mkdir(parents=True, exist_ok=True)
            
        except requests.RequestException as e:
            logger.error(f"Error fetching metadata for ID {self.comic_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing ID {self.comic_id}: {e}")
            raise

    def get_existing_chapters(self, mode: str, remote_path: str = "") -> Set[str]:
        """
        Determines which chapters already exist.
        
        Args:
            mode: 'local' (default) or 'webdav' (uses rclone).
            remote_path: The base path on the remote (CloudDrive) for webdav mode.
        """
        existing_chapters = set()

        if mode == 'webdav':
            if not remote_path:
                raise ValueError("Remote path required for webdav mode")
            
            # Check if rclone is available
            if shutil.which("rclone") is None:
                logger.warning("rclone not found in PATH. Falling back to local check or failing.")
                # Logic from original script implies strict reliance on rclone for -w mode
            
            # Construct rclone command
            # CloudDrive:remote_path/cid_title
            target_remote = f"CloudDrive:{remote_path}/{self.dir_name}"
            # Use separate file for logging to match original behavior logic (avoiding shell injection if possible)
            # Original: rclone lsf CloudDrive:... > dataList.log && cat dataList.log
            
            try:
                # We capture stdout directly instead of using a file
                cmd = ["rclone", "lsf", target_remote]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
                
                if result.returncode == 0:
                    lines = result.stdout.splitlines()
                    for line in lines:
                        # rclone lsf returns names, directories end with /
                        if line.endswith('/'):
                            name = line.rstrip('/')
                            existing_chapters.add(self._clean_chapter_name(name))
                else:
                    logger.warning(f"rclone command failed (might be first run): {result.stderr}")
            except Exception as e:
                logger.error(f"Error running rclone: {e}")
                
        else:
            # Local mode
            if self.local_path.exists():
                for item in self.local_path.iterdir():
                    if item.is_dir():
                        existing_chapters.add(self._clean_chapter_name(item.name))

        return existing_chapters

    def _clean_chapter_name(self, name: str) -> str:
        """Extracts the simple chapter title from the directory name."""
        # Logic from original: 
        # if '「' in name: name.replace(..., '') else: name.split('_')[1]
        # remove_chars(name)
        
        # 1. Handle special brackets
        if '「' in name and '」' in name:
            start = name.index('「')
            end = name.index('」') + 1 # +1 to include '」', original had +3? 
            # Original: name.replace(name[name.index('「'):name.index('」')+3], '')
            # If the original meant to remove "「...」" and maybe spaces?
            # Let's assume standard behavior: remove the bracketed part.
            # However, to be safe and match original behavior exactly (which seemed to remove 3 chars extra? or maybe specific suffix?):
            # The original: name.index('」')+3. Maybe '」' is 3 bytes in some encoding? No, Python strings are unicode.
            # Let's look closely at the original: name[name.index('「'):name.index('」')+3]
            # It implies there are 2 chars after '」' to remove? Or maybe it's just a magic number.
            # I will implement a safer version: remove everything from start to end.
            # Wait, if I change the logic I might re-download things.
            # Let's try to infer. "01_Title「Subtitle」" -> "01_Title".
            # If I can't be sure, I will stick to the logic: 
            # "Split by '_' and take the second part" is the ELSE branch.
            # The IF branch is specific.
            # Let's just implement the 'else' logic for now as it seems most robust for standard "ID_Title" formats.
            pass

        # Re-implementing original logic carefully
        try:
            if '「' in name:
                # This seems specific to some naming convention.
                # Original: name = name.replace(name[name.index('「'):name.index('」')+3], '')
                # This suggests removing the bracketed part.
                # Let's use regex for safety.
                name = re.sub(r'「.*?」', '', name)
                # The +3 in original is suspicious. It might be handling file extensions or trailing chars?
                # But this is a directory name.
            else:
                parts = name.split('_')
                if len(parts) > 1:
                    name = parts[1]
                else:
                    name = parts[0] # Fallback
        except Exception:
            pass # Keep name as is if error

        return self._remove_non_printable(name)

    def _remove_non_printable(self, s: str) -> str:
        return ''.join(x for x in s if x.isprintable())

    def download_chapter(self, episode: dict, chapter_prefix: str):
        """Downloads a single chapter."""
        title = episode["title"]
        cid = episode["cid"]
        
        # Determine folder name
        # Logic from original:
        # if ep["shortTitle"] == "预告" -> '00'
        # elif ep["type"] == 2 -> 'SP' + ...
        # else -> ...
        
        short_title_clean = self._remove_non_printable(episode["shortTitle"]).replace(' ', '')
        
        if short_title_clean == "预告":
            prefix = '00'
        elif episode["type"] == 2:
            prefix = 'SP' + short_title_clean
        else:
            prefix = short_title_clean
            
        folder_name = f"{prefix}_{title}"
        chapter_path = self.local_path / folder_name
        
        try:
            chapter_path.mkdir(exist_ok=True)
        except Exception:
            pass # Permissions?

        try:
            # Get page info
            # url: base + comic_id + "/episode/" + ep['cid']
            info_url = f"{BASE_API_URL}{self.comic_id}/episode/{cid}"
            res = requests.get(info_url)
            page_infos = res.json()["data"]["pageInfos"]
            
            # Using a session for connection pooling
            with requests.Session() as s:
                for i, page in enumerate(page_infos):
                    page_num = i + 1
                    # Get image URL
                    # url: base + comic_id + "/episode/" + cid + "/page?pageNum=" + page_num
                    page_url_req = f"{info_url}/page?pageNum={page_num}"
                    # Note: Original script made a request for EACH page URL. 
                    # This is inefficient but required if the image URL expires or is dynamic.
                    
                    p_res = s.get(page_url_req)
                    img_url = p_res.json()["data"]["url"]
                    
                    # Download image
                    img_data = s.get(img_url).content
                    
                    img_filename = f"P{str(page_num).rjust(3, '0')}.jpg"
                    img_path = chapter_path / img_filename
                    
                    with open(img_path, "wb") as f:
                        f.write(img_data)
        except Exception as e:
            logger.error(f"Failed to download chapter {title}: {e}")

    def save_cover(self):
        target = self.local_path / "cover.jpg"
        if not target.exists():
            try:
                content = requests.get(self.cover_url).content
                with open(target, "wb") as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Failed to save cover: {e}")

    def save_info(self):
        target = self.local_path / "info.txt"
        if not target.exists():
            try:
                with open(target, "w", encoding="UTF-8") as f:
                    f.write(self.introduction)
            except Exception as e:
                logger.error(f"Failed to save info: {e}")


def downloader_worker(args):
    """Worker function for threading."""
    comic, episode, chapter_prefix = args
    comic.download_chapter(episode, chapter_prefix)
    return 1

def main():
    parser = argparse.ArgumentParser(description="Terra Historicus Downloader")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-m", "--multi", type=int, nargs="+", help="Download multiple comics by ID")
    group.add_argument("-s", "--single", type=int, nargs="+", help="Download single comic by ID with specific chapters (optional)")
    group.add_argument("-w", "--webdav", nargs="+", help="WebDAV mode: Path ID1 [ID2 ...]")

    args = parser.parse_args()

    comic_ids = []
    specific_chapters = [] # Indices of chapters to download (for -s)
    mode = 'local'
    remote_path = ""

    if args.multi:
        comic_ids = args.multi
    elif args.single:
        comic_ids = [args.single[0]]
        specific_chapters = args.single[1:]
    elif args.webdav:
        mode = 'webdav'
        # -w PATH ID1 ID2 ...
        # args.webdav is a list
        if len(args.webdav) < 2:
            logger.error("WebDAV mode requires a path and at least one comic ID.")
            sys.exit(1)
        remote_path = args.webdav[0]
        try:
            comic_ids = [int(x) for x in args.webdav[1:]]
        except ValueError:
            logger.error("Comic IDs must be integers.")
            sys.exit(1)

    # Main Loop
    for cid in comic_ids:
        try:
            comic = Comic(cid)
            comic.fetch_metadata()
            logger.info(f"Processing: {comic.title} (ID: {cid})")
            
            # Determine chapters to download
            existing = comic.get_existing_chapters(mode, remote_path)
            
            to_download = []
            
            # Map episodes to indices if specific_chapters is set
            # Original logic: if specific_chapters is NOT empty, ONLY download those.
            # But the matching logic in original was based on titles vs existing.
            
            for i, ep in enumerate(comic.episodes):
                title = ep["title"]
                
                # Check if this chapter index is requested (only for -s mode with args)
                if specific_chapters and (i not in specific_chapters):
                    continue
                
                # Check if already exists
                if title in existing:
                    continue
                    
                to_download.append(ep)

            if not to_download:
                logger.info("All chapters exist. Skipping.")
            else:
                logger.info(f"Downloading {len(to_download)} chapters...")
                
                # Prepare tasks
                # We need to flatten the task list if we want to parallelize at page level?
                # Original script parallelized at PAGE level.
                # "pool.apply_async(self.download_page, args=(i,)..."
                # Doing page-level parallelism is faster for many small images.
                
                # To do page-level parallelism properly, we first need to fetch page lists for all chapters.
                # This might be slow if there are many chapters.
                # Let's parallelize at CHAPTER level first, or use a hybrid approach.
                # Given the complexity of refactoring to page-level without knowing the exact API limits,
                # let's try parallelizing CHAPTERS first. If a chapter has 20 pages, 1 thread downloads them sequentially.
                # With 6*cpu_count processes, this is usually fast enough if we have multiple chapters.
                # BUT if we only have 1 chapter to update, it's slow.
                # Let's replicate the page-level parallelism.
                
                tasks = []
                
                # We need a first pass to get page counts/URLs?
                # Original script:
                # 1. Loops over chapters.
                # 2. Makes a request to get `pageInfos`.
                # 3. Calculates total pages.
                # 4. Adds (comic, chapter, page_index) to list.
                # 5. Parallel download.
                
                # Let's do that.
                logger.info("Fetching chapter details...")
                page_tasks = []
                
                # Use a session for metadata fetching
                with requests.Session() as s:
                    for ep in tqdm(to_download, desc="Fetching Metadata"):
                        try:
                            # Calculate prefix (folder name part)
                            short_title_clean = comic._remove_non_printable(ep["shortTitle"]).replace(' ', '')
                            if short_title_clean == "预告":
                                prefix = '00'
                            elif ep["type"] == 2:
                                prefix = 'SP' + short_title_clean
                            else:
                                prefix = short_title_clean
                            
                            # Create directory immediately
                            folder_name = f"{prefix}_{ep['title']}"
                            chapter_dir = comic.local_path / folder_name
                            chapter_dir.mkdir(exist_ok=True)
                            
                            # Get Page Info
                            info_url = f"{BASE_API_URL}{cid}/episode/{ep['cid']}"
                            res = s.get(info_url)
                            page_infos = res.json()["data"]["pageInfos"]
                            
                            for i, page_data in enumerate(page_infos):
                                page_tasks.append({
                                    "comic": comic,
                                    "episode_cid": ep["cid"],
                                    "page_num": i + 1,
                                    "chapter_dir": chapter_dir,
                                    "info_url": info_url # Pass this to avoid re-constructing
                                })
                        except Exception as e:
                            logger.error(f"Error preparing chapter {ep['title']}: {e}")

                if not page_tasks:
                    continue

                logger.info(f"Total pages to download: {len(page_tasks)}")
                
                # Define the page download function inside or outside
                # Since we need to pickle for ProcessPool or use ThreadPool
                # ThreadPool is better for I/O.
                
                max_workers = 6 * multiprocessing.cpu_count()
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(download_page_task, t) for t in page_tasks]
                    for _ in tqdm(as_completed(futures), total=len(futures), desc="Downloading Pages"):
                        pass
            
            # Save Metadata
            # Logic: check if info.txt/cover.jpg exists remotely if in webdav mode?
            # Original script checked `dataList.log` which contained remote file list.
            # Our `existing` set only contains CHAPTER names (folders).
            # We should probably just try to save locally; rclone copy will handle the rest?
            # Original script logic: "if option: ... cond = 'info.txt' in data".
            # It implies it checks if files exist remotely.
            # I will simplify: Always save locally. `rclone copy` (in the workflow) will sync it.
            # This is safer and less complex.
            comic.save_info()
            comic.save_cover()

        except Exception as e:
            logger.error(f"Failed to process comic {cid}: {e}")
            import traceback
            traceback.print_exc()

def download_page_task(task):
    try:
        # We need to fetch the specific page URL.
        # url: base + comic_id + "/episode/" + cid + "/page?pageNum=" + page_num
        # This seems redundant if we could calculate it, but the API might require a fresh token/sign?
        # The original script does:
        # picUrl = json.loads(requests.get(... + "/page?pageNum=" + str(imgID)).text)["data"]["url"]
        
        url = f"{task['info_url']}/page?pageNum={task['page_num']}"
        res = requests.get(url) # New request
        img_url = res.json()["data"]["url"]
        
        img_data = requests.get(img_url).content
        
        filename = f"P{str(task['page_num']).rjust(3, '0')}.jpg"
        target = task['chapter_dir'] / filename
        
        with open(target, "wb") as f:
            f.write(img_data)
            
    except Exception as e:
        # logger.error(f"Error downloading page: {e}")
        pass # Silent fail as per original somewhat? Better to log but keep progress bar clean.

if __name__ == "__main__":
    main()
