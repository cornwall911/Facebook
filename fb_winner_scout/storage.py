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

        downloaded_paths = []
        for i, img_url in enumerate(post.image_urls):
            img_filename = f"img_{i+1}.jpg"
            target_path = post_folder / img_filename
            try:
                req = urllib.request.Request(img_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    "Referer": "https://www.facebook.com/",
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    with open(target_path, "wb") as f:
                        f.write(resp.read())
                downloaded_paths.append(str(target_path))
            except Exception as e:
                print(f"[Storage Warning] Failed to download image {i+1} for post {post.post_id}: {e}")

        post.local_images = downloaded_paths
        return downloaded_paths

    def save_to_json(self, posts: List[ScrapedPost], filename: str = "viral_posts.json") -> Path:
        """Saves or updates JSON file with scraped posts (deduplicated by post_id)."""
        file_path = self.reports_dir / filename
        existing_data = {}

        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    old_items = json.load(f)
                    for item in old_items:
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
                return [ScrapedPost(**item) for item in data]
        except Exception:
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
            "post_url", "caption", "local_images", "author", "group_id", "post_id"
        ]
        existing_cols = [c for c in cols_order if c in combined.columns]
        other_cols = [c for c in combined.columns if c not in existing_cols]
        combined = combined[existing_cols + other_cols]

        combined.to_excel(file_path, index=False)
        print(f"[Storage] Saved {len(combined)} total posts to Excel: {file_path}")
        return file_path
