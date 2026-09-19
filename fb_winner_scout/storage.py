import dataclasses
import os
import json
import urllib.request
from pathlib import Path
from typing import List
import pandas as pd
from fb_winner_scout.parser import ScrapedPost
from fb_winner_scout.config import ScoutConfig

class StorageManager:
    def __init__(self, config: ScoutConfig):
        self.config = config
        self.base_dir = config.output_dir
        self.images_dir = self.base_dir / "images"
        self.reports_dir = self.base_dir / "reports"

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

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
        """Saves or appends posts to a JSON database (deduplicated by post_id)."""
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
        """Loads all accumulated posts from the database."""
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
                
                # Filter only known fields
                filtered = {k: v for k, v in item.items() if k in known_fields}
                posts.append(ScrapedPost(**filtered))
            return posts
        except Exception as e:
            print(f"[Storage Warning] load_all_posts error: {e}")
            return []

    def save_to_excel(self, posts: List[ScrapedPost], filename: str = "viral_posts.xlsx") -> Path:
        """Saves or appends posts to an Excel spreadsheet (deduplicated by post_id)."""
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

        # Sort by reactions descending
        if "reactions_count" in combined.columns:
            combined = combined.sort_values(by="reactions_count", ascending=False)

        # Reorder columns for optimal user reading
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
