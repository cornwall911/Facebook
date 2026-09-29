import re
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Optional

# Eastern Arabic numerals mapping
AR_NUMS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

def parse_count(text: Optional[str]) -> int:
    """
    Parses reaction/comment/share counts into an integer.
    Supports English & Arabic: '1.2K', '250', '3.5M', '١٫٢ ألف', '٣٥٠'.
    """
    if not text:
        return 0
    
    clean = text.strip().translate(AR_NUMS)
    clean = clean.replace("٫", ".").replace(",", "").replace("،", "")

    # Check for Millions
    m_match = re.search(r"([\d\.]+)\s*(?:[mM]|مليون)", clean)
    if m_match:
        try:
            return int(float(m_match.group(1)) * 1000000)
        except ValueError:
            pass

    # Check for Thousands
    k_match = re.search(r"([\d\.]+)\s*(?:[kK]|ألف)", clean)
    if k_match:
        try:
            return int(float(k_match.group(1)) * 1000)
        except ValueError:
            pass

    # Standard digits
    digits = re.search(r"\d+", clean)
    if digits:
        try:
            return int(digits.group(0))
        except ValueError:
            pass

    return 0
 
def extract_affiliate_link(text: Optional[str]) -> str:
    """Extracts direct product/affiliate URLs (e.g. walmrt.us, fashlyst.com, walmart.com, amzn.to, a.co, amazon, mavely)."""
    if not text:
        return ""
    
    # Check for Facebook redirect links
    if "l.facebook.com/l.php" in text:
        try:
            m_fb = re.search(r"https?://l\.facebook\.com/l\.php\?[^\s\)\"\'>]+", text)
            if m_fb:
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(m_fb.group(0)).query)
                u = qs.get("u", [""])[0]
                if u:
                    text = text + " " + urllib.parse.unquote(u)
        except Exception:
            pass

    # High-priority affiliate & retailer domains
    pattern = (
        r"https?://(?:[a-zA-Z0-9\-\.]+\.)?"
        r"(?:walmrt\.us|fashlyst\.com|walmart\.com|amzn\.to|a\.co|amazon\.com|mavely\.app|"
        r"joinmavely\.com|liketk\.it|shopltk\.com|shopmy\.us|rstyle\.me|target\.com|bit\.ly|tinyurl\.com)"
        r"[^\s\)\"\'>]*"
    )
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        return m.group(0).rstrip(".,;)")
    
    m_gen = re.search(r"https?://[^\s\)\"\'>]+", text)
    if m_gen:
        cand = m_gen.group(0).rstrip(".,;)")
        if not ("facebook.com" in cand and "/l.php" not in cand):
            return cand
    return ""

@dataclass
class ScrapedPost:
    post_id: str
    post_url: str
    keyword: str
    group_id: str
    author: str = ""
    timestamp: str = ""
    caption: str = ""
    reactions_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    image_urls: List[str] = field(default_factory=list)
    local_images: List[str] = field(default_factory=list)
    is_product: bool = False
    product_category: str = ""
    amazon_query: str = ""
    winner_score: int = 0
    affiliate_url: str = ""
    generated_caption: str = ""
    clicks_count: int = 0

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
