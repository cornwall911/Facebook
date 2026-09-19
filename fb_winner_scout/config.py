import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class ScoutConfig:
    min_reactions: int = 10
    max_scrolls: int = 40
    max_posts_per_search: int = 100
    scroll_delay_min: float = 1.0
    scroll_delay_max: float = 2.0
    headless: bool = True
    output_dir: Path = field(default_factory=lambda: Path("data"))
    cookies_file: Optional[Path] = field(default_factory=lambda: Path("cookies.json") if Path("cookies.json").exists() else None)
    cookies_json_raw: Optional[str] = None
    proxy_url: Optional[str] = None
    user_data_dir: Optional[str] = None

    @classmethod
    def from_env(cls) -> "ScoutConfig":
        min_rx = int(os.environ.get("MIN_REACTIONS", "10"))
        max_scr = int(os.environ.get("MAX_SCROLLS", "40"))
        max_posts = int(os.environ.get("MAX_POSTS", "100"))
        headless_val = os.environ.get("HEADLESS", "true").lower() in ("true", "1", "yes")
        out_dir = Path(os.environ.get("OUTPUT_DIR", "data"))
        
        cookie_path = os.environ.get("FB_COOKIES_PATH")
        cookie_file = Path(cookie_path) if cookie_path else (Path("cookies.json") if Path("cookies.json").exists() else None)
        raw_cookie = os.environ.get("FB_COOKIES_JSON")
        proxy = os.environ.get("PROXY_URL")

        return cls(
            min_reactions=min_rx,
            max_scrolls=max_scr,
            max_posts_per_search=max_posts,
            headless=headless_val,
            output_dir=out_dir,
            cookies_file=cookie_file,
            cookies_json_raw=raw_cookie,
            proxy_url=proxy,
        )

    def load_cookies(self) -> List[dict]:
        """Loads and formats cookies into Playwright/Scrapling compatible list of dicts."""
        data = None
        if self.cookies_json_raw:
            try:
                data = json.loads(self.cookies_json_raw)
            except Exception as e:
                print(f"[Warning] Failed to parse FB_COOKIES_JSON: {e}")

        if not data and self.cookies_file and self.cookies_file.exists():
            try:
                with open(self.cookies_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"[Warning] Failed to read cookies file {self.cookies_file}: {e}")

        if not data:
            return []

        # Standardize cookies format for Playwright / Patchright
        formatted = []
        for c in data:
            cookie = {
                "name": c.get("name"),
                "value": c.get("value"),
                "domain": c.get("domain", ".facebook.com"),
                "path": c.get("path", "/"),
            }
            # Optional fields
            if "sameSite" in c:
                ss = str(c["sameSite"]).capitalize()
                if ss in ("Strict", "Lax", "None"):
                    cookie["sameSite"] = ss
            if "secure" in c:
                cookie["secure"] = bool(c["secure"])
            if "httpOnly" in c:
                cookie["httpOnly"] = bool(c["httpOnly"])
            if "expirationDate" in c and c["expirationDate"]:
                cookie["expires"] = int(c["expirationDate"])

            formatted.append(cookie)

        return formatted
