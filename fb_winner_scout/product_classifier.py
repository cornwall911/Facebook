import re
from typing import Tuple

# Non-product discussion patterns (exclusions)
NEGATIVE_PATTERNS = [
    r"\broute\b", r"\bhighway\b", r"\binterstate\b", r"\bdirections\b", r"\btraffic\b", r"\btoll\b",
    r"\bmileage\b", r"\bdriving to\b", r"\bstate to another\b", r"\bthrough dallas\b",
    r"\bcampground\b", r"\brv park\b", r"\bplaces to stay\b", r"\bcamp site\b", r"\bresort\b",
    r"\bwe officially did a thing\b", r"\bcomplete newbie", r"\bjust wanted to say hi\b",
    r"\bfirst time camping\b", r"\bprayers\b", r"\brip\b", r"\blemon law\b", r"\bdealership lied\b",
    r"\blawyer\b", r"\bsue\b", r"\bwarranty denied\b", r"\binterest rate\b", r"\bfinancing\b",
    r"\btowing capacity\b", r"\bpayload capacity\b", r"\btransmission fluid\b",
    r"\bbuy\s*back\b", r"\bnothing but trouble\b", r"\bavoid these lying\b", r"\bdeteriorating quickly\b"
]

# Physical product categories and their trigger terms
CATEGORIES = {
    "تنظيم وتخزين (Storage & Organization)": [
        "organizer", "storage", "bin", "basket", "shelf", "drawer", "holder", "cabinet",
        "rack", "hanger", "hook", "shoes", "sink topper", "collapsible", "tension rod", "magnetic"
    ],
    "أجهزة وإلكترونيات (Gadgets & Power)": [
        "gadget", "device", "solar", "battery", "generator", "inverter", "charger", "plug",
        "heater", "fan", "ac", "air conditioner", "dehumidifier", "ice maker", "tpms", "camera", "gps", "monitor"
    ],
    "إكسسوارات وحلول ذكية (Smart Accessories & Hacks)": [
        "hack", "upgrade", "game changer", "worth every penny", "must have", "amazon find", "bought on amazon",
        "pool", "ladder", "shade", "blind", "mat", "cushion", "cover", "pet", "shower", "faucet", "lock"
    ],
    "معدات وأمان (RV Gear & Hardware)": [
        "stabilizer", "jack", "chock", "leveler", "hitch", "hose", "water filter", "regulator",
        "surge protector", "adapter", "seal", "vent", "skillet", "grill"
    ]
}

# General product signals
POSITIVE_SIGNALS = [
    "amazon", "bought", "ordered", "purchased", "got this", "delivered", "worth every penny",
    "game changer", "hack", "organizer", "gadget", "device", "upgrade", "tool", "item",
    "portable", "compact", "holder", "ladder", "solar", "leveler", "chock", "stabilizer",
    "heater", "fan", "hose", "filter", "light", "mat", "cover", "lock", "adapter",
    "sink", "faucet", "grill", "storage", "bin", "shelf", "battery", "generator",
    "link in comments", "link below", "$", "dollars", "review", "unboxing", "install",
    "installed", "accessory", "accessories", "must have", "flip", "collapsible", "magnetic"
]

def classify_post_product(caption: str, image_count: int, keyword: str = "") -> Tuple[bool, str, str, int]:
    """
    Evaluates whether a scraped Facebook post represents a physical winning product.
    Returns:
        is_product (bool): True if confirmed physical product
        category (str): Product category
        search_query (str): Clean search term for Amazon 1-click search
        score (int): Winner score out of 100
    """
    # 1. Image is strictly required for e-commerce winner scouting
    if image_count < 1:
        return False, "غير مؤهل (بدون صور)", "", 0

    text = (caption or "").lower()
    kw = (keyword or "").lower()

    # 2. Check negative exclusions
    for neg in NEGATIVE_PATTERNS:
        if re.search(neg, text):
            return False, "استبعاد (نقاش/سفر/شكوى)", "", 0

    # 3. Detect category & positive signals
    matched_category = "منتج فيزيائي (Physical Product)"
    highest_cat_matches = 0

    for cat_name, terms in CATEGORIES.items():
        matches = sum(1 for term in terms if term in text or term in kw)
        if matches > highest_cat_matches:
            highest_cat_matches = matches
            matched_category = cat_name

    # Check general positive signals
    signal_count = sum(1 for sig in POSITIVE_SIGNALS if sig in text or sig in kw)
    if "$" in caption or re.search(r"\b\d+\s*(?:dollars|bucks)\b", text):
        signal_count += 2

    # If search keyword is explicitly a product keyword (e.g. amazon find, organizer)
    is_product_keyword = any(k in kw for k in ["amazon", "organizer", "gadget", "upgrade", "storage", "hack", "must have"])
    
    if signal_count >= 1 or is_product_keyword or highest_cat_matches >= 1:
        # Extract a clean Amazon search query
        query = _extract_amazon_search_query(caption, keyword)
        
        # Calculate winner score (base 60 + signals)
        score = min(100, 60 + (signal_count * 8) + (min(image_count, 3) * 5))
        return True, matched_category, query, score

    return False, "غير مؤكد (نقاش عام)", "", 0

def _extract_amazon_search_query(caption: str, keyword: str) -> str:
    """Extracts a succinct, high-converting 2-4 word Amazon search term."""
    text = caption.lower()
    
    # Specific common RV winners
    if "pool" in text: return "rv collapsible pet pool"
    if "ladder" in text: return "bunk bed trampoline ladder"
    if "stabilizer" in text or "jack" in text or "wobble" in text or "shake" in text: return "rv stabilizer x chock"
    if "fan" in text or "cool" in text: return "rv 12v portable bunk fan"
    if "heater" in text: return "camper space heater safe"
    if "tailgate" in text: return "tailgate jack clearance flip"
    if "sink" in text: return "rv sink cover cutting board topper"
    if "shoe" in text or "organizer" in text: return "rv hanging shoe organizer"
    if "dehumidifier" in text: return "rv small dehumidifier"
    if "oxidation" in text or "fiberglass" in text: return "rv fiberglass oxidation remover"
    if "water filter" in text: return "rv inline water filter"
    if "level" in text: return "rv curved leveling blocks"

    # Fallback: combine keyword with RV
    clean_kw = re.sub(r"[^a-zA-Z0-9\s]", "", keyword).strip()
    if clean_kw:
        return f"rv {clean_kw}"
    return "rv must haves amazon"
