import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import List, Optional

# Eastern Arabic numerals mapping
AR_NUMS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

def parse_count(text: Optional[str]) -> Optional[int]:
    """
    Parses reaction/comment/share counts into an integer.
    Supports English & Arabic: '1.2K', '250', '3.5M', '١٫٢ ألف', '٣٥٠', 'Like: 20 people'.
    Returns None if no valid count could be read (never a default zero).
    """
    if text is None:
        return None
    
    clean = str(text).strip()
    if not clean:
        return None

    clean = clean.translate(AR_NUMS)
    clean = clean.replace("٫", ".").replace(",", "").replace("،", "")

    # Check for Millions: e.g. '1.5M', '2 million', '2 مليون'
    m_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:[mM]|مليون)", clean)
    if m_match:
        try:
            return int(float(m_match.group(1)) * 1000000)
        except ValueError:
            pass

    # Check for Thousands: e.g. '1.2K', '15k', '١٫٢ ألف'
    k_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:[kK]|ألف)", clean)
    if k_match:
        try:
            return int(float(k_match.group(1)) * 1000)
        except ValueError:
            pass

    # Standard digits (require at least one digit, word boundary or isolated)
    digits = re.search(r"\b(\d+)\b", clean)
    if digits:
        try:
            return int(digits.group(1))
        except ValueError:
            pass

    return None

def extract_outbound_link(raw_url_or_text: Optional[str]) -> Optional[str]:
    """
    Extracts and redirect-decodes outbound product URLs from Facebook post content.
    - Decodes l.facebook.com/l.php?u= redirects.
    - Strictly drops any links pointing to facebook.com, instagram.com, fb.me, meta.com, etc.
    - Returns the clean outbound URL or None (never an invented Amazon search query).
    """
    if not raw_url_or_text:
        return None
    
    text = str(raw_url_or_text).strip()
    if not text:
        return None

    # Handle l.facebook.com redirect wrapper
    if "l.facebook.com/l.php" in text:
        m = re.search(r"[?&]u=([^&]+)", text)
        if m:
            try:
                decoded = urllib.parse.unquote(m.group(1))
                text = decoded
            except Exception:
                pass

    # Extract HTTP/HTTPS candidate
    m_url = re.search(r"https?://[^\s\)\"\'>]+", text)
    if not m_url:
        return None

    cand = m_url.group(0).rstrip(".,;)>\"'")

    # Strip Facebook tracking parameters (__cft__, __tn__, rdid)
    cand = cand.split("&rdid=")[0].split("?rdid=")[0]
    if "?" in cand and ("__cft__" in cand or "__tn__" in cand):
        cand = cand.split("?")[0]

    # Validate destination domain
    try:
        parsed = urllib.parse.urlparse(cand)
        netloc = (parsed.netloc or "").lower()
        if not netloc:
            return None

        # Exclude internal Facebook/Meta network domains
        blocked_domains = [
            "facebook.com", "m.facebook.com", "l.facebook.com",
            "instagram.com", "fb.me", "fb.com", "fb.watch",
            "messenger.com", "threads.net", "meta.com"
        ]
        for b in blocked_domains:
            if netloc == b or netloc.endswith("." + b):
                return None

        return cand
    except Exception:
        return None

def parse_posted_at(raw_time: Optional[str], ref_datetime: Optional[datetime] = None) -> Optional[str]:
    """
    Parses Facebook relative or date strings into ISO 8601 UTC ('YYYY-MM-DDTHH:MM:SSZ').
    Examples: '6h', '6 hours ago', '2d', '2 days ago', '45m', 'Yesterday at 14:20'.
    Returns None if timestamp cannot be determined.
    """
    if not raw_time:
        return None
    
    t = str(raw_time).strip()
    if not t:
        return None

    # If already ISO-like string
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", t):
        return t

    now = ref_datetime or datetime.now(timezone.utc)

    # Relative minutes: e.g. '15m', '15 mins ago', '15 minutes ago'
    m_mins = re.search(r"^(\d+)\s*(?:m|mins?|minutes?(?:\s+ago)?)$", t, re.I)
    if m_mins:
        dt = now - timedelta(minutes=int(m_mins.group(1)))
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Relative hours: e.g. '6h', '6 hrs ago', '6 hours ago'
    m_hours = re.search(r"^(\d+)\s*(?:h|hrs?|hours?(?:\s+ago)?)$", t, re.I)
    if m_hours:
        dt = now - timedelta(hours=int(m_hours.group(1)))
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Relative days: e.g. '2d', '2 days ago'
    m_days = re.search(r"^(\d+)\s*(?:d|days?(?:\s+ago)?)$", t, re.I)
    if m_days:
        dt = now - timedelta(days=int(m_days.group(1)))
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    # 'Yesterday'
    if "yesterday" in t.lower():
        dt = now - timedelta(days=1)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return None

@dataclass
class SourcePost:
    """
    Output contract for public/source_posts.json.
    Strictly represents real live scraped posts with real engagement numbers
    and authentic outbound product links.
    """
    post_id: str
    post_url: str
    group: str
    group_name: str
    caption: str
    product_url: str
    reactions: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    posted_at: Optional[str] = None
    image_url: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    data_source: str = "live"

    def to_dict(self) -> dict:
        return {
            "post_id": str(self.post_id),
            "post_url": self.post_url,
            "group": str(self.group),
            "group_name": self.group_name,
            "caption": self.caption,
            "product_url": self.product_url,
            "reactions": self.reactions,
            "comments": self.comments,
            "shares": self.shares,
            "posted_at": self.posted_at,
            "image_url": self.image_url,
            "scraped_at": self.scraped_at,
            "data_source": self.data_source
        }

@dataclass
class ScrapedPost:
    post_id: str
    post_url: str
    keyword: str
    group_id: str
    author: str = ""
    timestamp: str = ""
    caption: str = ""
    reactions_count: Optional[int] = None
    comments_count: Optional[int] = None
    shares_count: Optional[int] = None
    image_urls: List[str] = field(default_factory=list)
    local_images: List[str] = field(default_factory=list)
    is_product: bool = False
    product_category: str = ""
    amazon_query: str = ""
    winner_score: int = 0
    affiliate_url: str = ""
    generated_caption: str = ""
    clicks_count: Optional[int] = None

    def to_dict(self) -> dict:
        imgs = self.image_urls if isinstance(self.image_urls, list) else [u.strip() for u in str(self.image_urls).split("; ") if u.strip()]
        locs = self.local_images if isinstance(self.local_images, list) else [u.strip() for u in str(self.local_images).split("; ") if u.strip()]
        return {
            "post_id": self.post_id,
            "post_url": self.post_url,
            "keyword": self.keyword,
            "group_id": self.group_id,
            "author": self.author,
            "timestamp": self.timestamp,
            "caption": self.caption,
            "generated_caption": self.generated_caption,
            "reactions_count": self.reactions_count,
            "comments_count": self.comments_count,
            "shares_count": self.shares_count,
            "clicks_count": self.clicks_count,
            "is_product": self.is_product,
            "product_category": self.product_category,
            "amazon_query": self.amazon_query,
            "winner_score": self.winner_score,
            "affiliate_url": self.affiliate_url,
            "image_urls": "; ".join(imgs),
            "local_images": "; ".join(locs),
        }


def parse_post_with_scrapling(html: str, group_slug: str = "", group_name: str = ""):
    """
    Parses a single Facebook post HTML container using Scrapling's Selector.
    Extracts post_id, clean post_url, caption text, outbound product link,
    engagement metrics (reactions, comments, shares), timestamp, and image URL.
    Returns SourcePost if valid post_id and outbound product link exist, else None.
    """
    if not html or len(html.strip()) < 20:
        return None

    try:
        from scrapling.parser import Selector
        sel = Selector(html)
    except Exception:
        return None

    # 1. Post ID and Post URL
    post_id = None
    post_url = None
    
    candidate_links = sel.css("a[href*='/posts/'], a[href*='/permalink/'], a[href*='multi_permalinks=']::attr(href)").getall()
    for l in candidate_links:
        m = re.search(r"/posts/(\d+)", l) or re.search(r"multi_permalinks=(\d+)", l) or re.search(r"/permalink/(\d+)", l)
        if m:
            post_id = m.group(1)
            base = l.split("?")[0].rstrip("/")
            post_url = base + "/" if base.startswith("http") else f"https://www.facebook.com{base}/"
            break

    if not post_id:
        return None

    # 2. Caption
    caption = ""
    msg_nodes = sel.css("div[dir='auto'][style*='text-align'], div[data-ad-preview='message'], div[data-ad-comet-preview='message']")
    if msg_nodes:
        caption = " ".join([t.strip() for t in msg_nodes[0].css("::text").getall() if t.strip()])
    if not caption:
        dir_nodes = sel.css("div[dir='auto']")
        for d in dir_nodes:
            t = " ".join([txt.strip() for txt in d.css("::text").getall() if txt.strip()])
            if len(t) > 25 and not any(w in t for w in ["Like", "Comment", "Share"]):
                caption = t
                break

    # 3. Outbound links
    outbound_links = []
    for href in sel.css("a[href]::attr(href)").getall():
        cleaned = extract_outbound_link(href)
        if cleaned and cleaned not in outbound_links:
            outbound_links.append(cleaned)

    # Search within caption text for short links
    if caption:
        for m_url in re.findall(r"https?://[^\s\)'\"]+", caption):
            cleaned = extract_outbound_link(m_url)
            if cleaned and cleaned not in outbound_links:
                outbound_links.append(cleaned)

    if not outbound_links:
        return None

    product_url = outbound_links[0]

    # 4. Reactions
    reactions = None
    aria_texts = sel.css("[aria-label]::attr(aria-label)").getall()
    for a in aria_texts:
        if re.search(r"like|reactions?|people", a, re.I) and re.search(r"\d+", a):
            reactions = parse_count(a)
            if reactions is not None:
                break
    if reactions is None:
        tb_texts = sel.css("span[role='toolbar'] *::text").getall()
        if tb_texts:
            reactions = parse_count(" ".join(tb_texts))

    # 5. Comments & Shares
    comments = None
    shares = None
    for t in sel.css("span::text, div::text").getall():
        t = t.strip()
        m_c = re.match(r"^([\d\.,kKmM]+)\s*comments?$", t, re.I)
        if m_c and comments is None:
            comments = parse_count(m_c.group(1))
        m_s = re.match(r"^([\d\.,kKmM]+)\s*shares?$", t, re.I)
        if m_s and shares is None:
            shares = parse_count(m_s.group(1))

    # 6. Timestamp
    posted_at = None
    for t in sel.css(f"a[href*='{post_id}'] *::text, a[href*='/posts/'] *::text").getall():
        p_time = parse_posted_at(t.strip())
        if p_time:
            posted_at = p_time
            break

    # 7. Image
    imgs = sel.css("img[src*='scontent'], img[src*='fbcdn']::attr(src)").getall()
    image_url = imgs[0] if imgs else None

    if not post_url:
        post_url = f"https://www.facebook.com/groups/{group_slug}/posts/{post_id}/"

    return SourcePost(
        post_id=post_id,
        post_url=post_url,
        group=group_slug,
        group_name=group_name or group_slug,
        caption=caption,
        product_url=product_url,
        reactions=reactions,
        comments=comments,
        shares=shares,
        posted_at=posted_at,
        image_url=image_url,
        scraped_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        data_source="live"
    )
