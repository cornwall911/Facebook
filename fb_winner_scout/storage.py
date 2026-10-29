import dataclasses
import os
import json
import urllib.request
from pathlib import Path
from typing import List, Dict, Optional, Any
import pandas as pd
from fb_winner_scout.parser import ScrapedPost, SourcePost
from fb_winner_scout.config import ScoutConfig

class StorageManager:
    def __init__(self, config: ScoutConfig):
        self.config = config
        self.base_dir = config.output_dir
        self.images_dir = self.base_dir / "images"
        self.reports_dir = self.base_dir / "reports"
        self.public_dir = Path("public")

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.public_dir.mkdir(parents=True, exist_ok=True)

        self.source_posts_path = self.public_dir / "source_posts.json"
        self.run_status_path = self.public_dir / "run_status.json"

    # =========================================================================
    # CONTRACT B: public/source_posts.json (Live Scraped Posts)
    # =========================================================================

    def load_source_posts(self) -> List[SourcePost]:
        """Loads all existing live source posts from public/source_posts.json."""
        if not self.source_posts_path.exists():
            return []
        try:
            with open(self.source_posts_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            posts = []
            known_fields = {f.name for f in dataclasses.fields(SourcePost)}
            for item in data:
                filtered = {k: v for k, v in item.items() if k in known_fields}
                posts.append(SourcePost(**filtered))
            return posts
        except Exception as e:
            print(f"[Storage Warning] Failed to load {self.source_posts_path}: {e}")
            return []

    def save_source_posts(self, posts: List[SourcePost]) -> Path:
        """Saves a list of SourcePost objects to public/source_posts.json."""
        data = [p.to_dict() for p in posts]
        with open(self.source_posts_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[Storage] Saved {len(data)} live posts to {self.source_posts_path}")
        return self.source_posts_path

    def merge_source_posts(self, new_posts: List[SourcePost]) -> List[SourcePost]:
        """
        Deduplicates posts by post_id across runs:
        - If post_id exists: keeps first_seen/posted_at, updates reactions/comments/shares
          with latest non-null values, and updates scraped_at.
        - If post_id is new: appends it.
        """
        existing = self.load_source_posts()
        merged_map: Dict[str, SourcePost] = {p.post_id: p for p in existing}

        for np in new_posts:
            if np.post_id in merged_map:
                old = merged_map[np.post_id]
                # Update engagement metrics if new value was successfully read
                if np.reactions is not None:
                    old.reactions = np.reactions
                if np.comments is not None:
                    old.comments = np.comments
                if np.shares is not None:
                    old.shares = np.shares
                if np.image_url and not old.image_url:
                    old.image_url = np.image_url
                if not old.posted_at and np.posted_at:
                    old.posted_at = np.posted_at
                old.scraped_at = np.scraped_at
            else:
                merged_map[np.post_id] = np

        merged_list = list(merged_map.values())
        self.save_source_posts(merged_list)
        return merged_list

    # =========================================================================
    # CONTRACT C: public/run_status.json
    # =========================================================================

    def save_run_status(
        self,
        started_at: str,
        finished_at: str,
        session: str,
        groups: List[Dict[str, Any]],
        total_written: int,
        errors: Optional[List[str]] = None,
        data_source: str = "live"
    ) -> Path:
        """
        Writes the run status file public/run_status.json.
        Always written at the end of every run, including when it fails.
        """
        status_payload = {
            "started_at": started_at,
            "finished_at": finished_at,
            "session": session,
            "groups": groups,
            "total_written": total_written,
            "data_source": data_source,
            "errors": errors or []
        }
        with open(self.run_status_path, "w", encoding="utf-8") as f:
            json.dump(status_payload, f, ensure_ascii=False, indent=2)
        print(f"[Storage] Run status recorded in {self.run_status_path}")
        return self.run_status_path

    # =========================================================================
    # LEGACY / ARTIFACT HELPERS (Images, Excel, Internal Reports)
    # =========================================================================

    def download_post_images(self, post: ScrapedPost) -> List[str]:
        """Downloads full-res images for a post into its dedicated folder."""
        if not post.image_urls:
            return []

        safe_kw = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in post.keyword)[:20]
        post_folder = self.images_dir / f"{safe_kw}_{post.post_id}"
        post_folder.mkdir(parents=True, exist_ok=True)

        downloaded = []
        for idx, img_url in enumerate(post.image_urls, 1):
            if not img_url.startswith("http"):
                continue
            ext = ".jpg"
            out_file = post_folder / f"img_{idx}{ext}"
            if not out_file.exists():
                try:
                    req = urllib.request.Request(
                        img_url,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    )
                    with urllib.request.urlopen(req, timeout=10) as response, open(out_file, "wb") as f:
                        f.write(response.read())
                    downloaded.append(str(out_file))
                except Exception as e:
                    print(f"[Storage Warning] Failed to download {img_url[:40]}...: {e}")
            else:
                downloaded.append(str(out_file))

        post.local_images = downloaded
        return downloaded

    def save_to_json(self, posts: List[ScrapedPost], filename: str = "viral_posts.json") -> Path:
        """Saves posts to internal reports json."""
        file_path = self.reports_dir / filename
        existing_data = {}

        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for item in json.load(f):
                        existing_data[item["post_id"]] = item
            except Exception:
                pass

        for p in posts:
            existing_data[p.post_id] = p.to_dict()

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(list(existing_data.values()), f, ensure_ascii=False, indent=2)

        print(f"[Storage] Saved {len(existing_data)} total posts to JSON: {file_path}")
        return file_path

    def load_all_posts(self, filename: str = "viral_posts.json") -> List[ScrapedPost]:
        """Loads posts from internal reports json."""
        file_path = self.reports_dir / filename
        if not file_path.exists():
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            posts = []
            known_fields = {f.name for f in dataclasses.fields(ScrapedPost)}
            for item in data:
                iu = item.get("image_urls", [])
                if isinstance(iu, str):
                    if iu.startswith("h; t; t; p"):
                        iu = "".join([part for part in iu.split("; ")])
                    item["image_urls"] = [u.strip() for u in iu.split("; ") if u.strip()]
                li = item.get("local_images", [])
                if isinstance(li, str):
                    if li.startswith("d; a; t; a"):
                        li = "".join([part for part in li.split("; ")])
                    item["local_images"] = [l.strip() for l in li.split("; ") if l.strip()]
                
                filtered = {k: v for k, v in item.items() if k in known_fields}
                posts.append(ScrapedPost(**filtered))
            return posts
        except Exception as e:
            print(f"[Storage Warning] load_all_posts error: {e}")
            return []

    def save_to_excel(self, posts: List[ScrapedPost], filename: str = "viral_posts.xlsx") -> Path:
        """Saves posts to an Excel spreadsheet."""
        file_path = self.reports_dir / filename
        new_df = pd.DataFrame([p.to_dict() for p in posts])

        if file_path.exists():
            try:
                old_df = pd.read_excel(file_path)
                combined = pd.concat([old_df, new_df], ignore_index=True)
                combined = combined.drop_duplicates(subset=["post_id"], keep="last")
            except Exception:
                combined = new_df
        else:
            combined = new_df

        if "reactions_count" in combined.columns:
            combined = combined.sort_values(by="reactions_count", ascending=False)

        cols_order = [
            "keyword", "reactions_count", "comments_count", "shares_count",
            "post_url", "caption", "generated_caption", "local_images", "author", "group_id", "post_id"
        ]
        existing_cols = [c for c in cols_order if c in combined.columns]
        other_cols = [c for c in combined.columns if c not in existing_cols]
        combined = combined[existing_cols + other_cols]

        combined.to_excel(file_path, index=False)
        print(f"[Storage] Saved {len(combined)} total posts to Excel: {file_path}")
        return file_path
