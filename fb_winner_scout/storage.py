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

    def load_all_dashboard_posts(self) -> list:
        """
        Unifies and normalizes all available post datasets:
        1. Historical viral posts (public/viral_posts.json)
        2. Verified catalog posts (public/catalog_posts.json)
        3. Live scraped source posts (public/source_posts.json)

        Returns deduplicated list with standardized fields so frontend
        never crashes or filters out items inadvertently.
        """
        all_posts_map = {}

        def _read_json_file(p: Path) -> list:
            if not p.exists():
                return []
            try:
                with open(p, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    return content if isinstance(content, list) else []
            except Exception as e:
                print(f"[Storage Warning] Could not read {p}: {e}")
                return []

        # 1. Historical viral posts
        v_posts = _read_json_file(self.public_dir / "viral_posts.json") or _read_json_file(self.reports_dir / "viral_posts.json")
        for item in v_posts:
            pid = str(item.get("post_id", "")).strip()
            if pid:
                all_posts_map[pid] = dict(item)

        # 2. Verified catalog posts
        c_posts = _read_json_file(self.public_dir / "catalog_posts.json") or _read_json_file(self.reports_dir / "catalog_posts.json")
        for item in c_posts:
            pid = str(item.get("post_id", "")).strip()
            if pid:
                if pid in all_posts_map:
                    all_posts_map[pid].update(item)
                else:
                    all_posts_map[pid] = dict(item)

        # 3. Live source posts (highest fidelity for live metrics)
        s_posts = _read_json_file(self.source_posts_path)
        for item in s_posts:
            pid = str(item.get("post_id", "")).strip()
            if pid:
                if pid in all_posts_map:
                    all_posts_map[pid].update(item)
                else:
                    all_posts_map[pid] = dict(item)

        # Normalize each item
        normalized = []
        for pid, p in all_posts_map.items():
            product_url = p.get("product_url") or p.get("affiliate_url") or ""
            affiliate_url = p.get("affiliate_url") or p.get("product_url") or ""

            # Standardize reactions / comments / shares
            rx = p.get("reactions") if p.get("reactions") is not None else p.get("reactions_count")
            cm = p.get("comments") if p.get("comments") is not None else p.get("comments_count")
            sh = p.get("shares") if p.get("shares") is not None else p.get("shares_count")

            # Standardize images
            imgs_val = p.get("image_urls")
            if isinstance(imgs_val, list):
                imgs_str = "; ".join(imgs_val)
                first_img = imgs_val[0] if imgs_val else (p.get("image_url") or "")
            elif isinstance(imgs_val, str) and imgs_val:
                imgs_str = imgs_val
                first_img = imgs_val.split("; ")[0].strip()
            else:
                first_img = p.get("image_url") or ""
                imgs_str = first_img

            is_prod = bool(p.get("is_product") or product_url or affiliate_url)

            norm_item = {
                "post_id": pid,
                "post_url": p.get("post_url") or f"https://www.facebook.com/posts/{pid}/",
                "keyword": p.get("keyword") or p.get("group_name") or "RV Product",
                "group_id": p.get("group_id") or p.get("group") or "RV Community",
                "group_name": p.get("group_name") or p.get("group_id") or "RV Living & Camping",
                "author": p.get("author") or "RV Community Member",
                "caption": p.get("caption") or "",
                "generated_caption": p.get("generated_caption") or "",
                "product_url": product_url,
                "affiliate_url": affiliate_url,
                "reactions": rx,
                "reactions_count": rx or 0,
                "comments": cm,
                "comments_count": cm or 0,
                "shares": sh,
                "shares_count": sh or 0,
                "clicks_count": p.get("clicks_count", 0),
                "is_product": is_prod,
                "product_category": p.get("product_category") or "منتجات وأجهزة الكرفان",
                "amazon_query": p.get("amazon_query") or p.get("keyword") or "rv gadget",
                "winner_score": p.get("winner_score") or 95,
                "image_urls": imgs_str,
                "image_url": first_img,
                "posted_at": p.get("posted_at") or p.get("timestamp") or "",
                "data_source": p.get("data_source") or "live"
            }
            normalized.append(norm_item)

        print(f"[Storage] Loaded {len(normalized)} unified posts for dashboard.")
        return normalized

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
