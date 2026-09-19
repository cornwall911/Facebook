import re
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
            "reactions_count": self.reactions_count,
            "comments_count": self.comments_count,
            "shares_count": self.shares_count,
            "is_product": self.is_product,
            "product_category": self.product_category,
            "amazon_query": self.amazon_query,
            "winner_score": self.winner_score,
            "image_urls": "; ".join(imgs),
            "local_images": "; ".join(locs),
        }
