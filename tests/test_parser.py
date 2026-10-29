from pathlib import Path
from bs4 import BeautifulSoup
from fb_winner_scout.parser import (
    parse_count,
    extract_outbound_link,
    parse_posted_at,
    SourcePost
)
from fb_winner_scout.storage import StorageManager
from fb_winner_scout.config import ScoutConfig

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_parse_count_standard():
    assert parse_count("250") == 250
    assert parse_count("1.2K") == 1200
    assert parse_count("15.5k") == 15500
    assert parse_count("2M") == 2000000
    assert parse_count("٣٥٠") == 350
    assert parse_count("١٫٢ ألف") == 1200
    assert parse_count("0") == 0
    assert parse_count("45 comments") == 45
    assert parse_count("1.4K shares") == 1400

def test_parse_count_null_and_invalid():
    # Contract: unreadable or absent counts must return None (never a default 0)
    assert parse_count(None) is None
    assert parse_count("") is None
    assert parse_count("   ") is None
    assert parse_count("Like") is None
    assert parse_count("Comment") is None
    assert parse_count("Share") is None

def test_parse_count_facebook_aria():
    assert parse_count("Like: 20 people") == 20
    assert parse_count("All reactions: 11") == 11
    assert parse_count("1.2K reactions") == 1200

def test_outbound_link_decoding():
    # l.facebook.com redirect decoding
    raw_fb_redirect = "https://l.facebook.com/l.php?u=https%3A%2F%2Fwalmrt.us%2F4eojgm9&h=mock_token&__tn__=-UK-R"
    decoded = extract_outbound_link(raw_fb_redirect)
    assert decoded == "https://walmrt.us/4eojgm9"

    raw_amazon = "https://l.facebook.com/l.php?u=https%3A%2F%2Famzn.to%2F3abc123&h=token"
    assert extract_outbound_link(raw_amazon) == "https://amzn.to/3abc123"

def test_outbound_link_internal_fb_dropped():
    # Internal Facebook/Instagram links must NOT be treated as product links
    assert extract_outbound_link("https://www.facebook.com/groups/123/posts/456/") is None
    assert extract_outbound_link("https://www.instagram.com/p/abc/") is None
    assert extract_outbound_link("https://fb.me/something") is None
    assert extract_outbound_link(None) is None
    assert extract_outbound_link("") is None

def test_post_with_link_fixture():
    html = (FIXTURES_DIR / "post_with_link.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Extract link
    links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
    valid_outbound = None
    for l in links:
        clean = extract_outbound_link(l)
        if clean:
            valid_outbound = clean
            break
    
    assert valid_outbound == "https://walmrt.us/4eojgm9"

    # 2. Extract reactions & comments
    rx_el = soup.find(attrs={"aria-label": lambda a: a and "like" in a.lower()})
    rx_count = parse_count(rx_el["aria-label"])
    assert rx_count == 11

    cm_text = soup.find(string=lambda t: t and "comments" in t)
    cm_count = parse_count(cm_text)
    assert cm_count == 16

def test_post_no_link_dropped():
    # Posts without an outbound product link must have no valid outbound URL and be dropped
    html = (FIXTURES_DIR / "post_no_link.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    
    links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
    valid_outbound = None
    for l in links:
        clean = extract_outbound_link(l)
        if clean:
            valid_outbound = clean
            break
            
    assert valid_outbound is None

def test_post_k_reactions_fixture():
    html = (FIXTURES_DIR / "post_k_reactions.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    rx_el = soup.find(attrs={"aria-label": lambda a: a and "reactions" in a.lower()})
    assert parse_count(rx_el["aria-label"]) == 1200

    sh_text = soup.find(string=lambda t: t and "shares" in t)
    assert parse_count(sh_text) == 1400

    link_el = soup.find("a", href=lambda h: h and "l.facebook.com" in h)
    assert extract_outbound_link(link_el["href"]) == "https://amzn.to/3abc123"

def test_see_more_expansion_selector():
    html = (FIXTURES_DIR / "post_see_more.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    
    see_more = soup.find(lambda tag: tag.name == "div" and tag.get_text(strip=True) in ("See more", "See More", "عرض المزيد"))
    assert see_more is not None
    assert see_more["role"] == "button"

def test_source_post_contract_and_dedup(tmp_path):
    storage = StorageManager(ScoutConfig(output_dir=tmp_path))
    storage.public_dir = tmp_path / "public"
    storage.public_dir.mkdir(parents=True, exist_ok=True)
    storage.source_posts_path = storage.public_dir / "source_posts.json"

    p1 = SourcePost(
        post_id="1074562088508661",
        post_url="https://www.facebook.com/groups/466434735988069/posts/1074562088508661/",
        group="466434735988069",
        group_name="RV Living & Storage ideas",
        caption="Full original caption verbatim",
        product_url="https://walmrt.us/4eojgm9",
        reactions=11,
        comments=16,
        shares=None,
        posted_at="2026-10-27T18:40:00Z",
        image_url="https://scontent.xx.fbcdn.net/img.jpg",
        scraped_at="2026-10-29T02:00:00Z",
        data_source="live"
    )

    # Initial save
    merged = storage.merge_source_posts([p1])
    assert len(merged) == 1
    assert merged[0].reactions == 11
    assert merged[0].data_source == "live"
    assert merged[0].shares is None

    # Second run: same post updated with higher reactions and a newly read shares count
    p1_updated = SourcePost(
        post_id="1074562088508661",
        post_url="https://www.facebook.com/groups/466434735988069/posts/1074562088508661/",
        group="466434735988069",
        group_name="RV Living & Storage ideas",
        caption="Full original caption verbatim",
        product_url="https://walmrt.us/4eojgm9",
        reactions=25,
        comments=18,
        shares=3,
        posted_at=None, # Should preserve old posted_at
        image_url=None,
        scraped_at="2026-10-29T04:00:00Z",
        data_source="live"
    )

    merged2 = storage.merge_source_posts([p1_updated])
    assert len(merged2) == 1 # Deduplicated by post_id
    assert merged2[0].reactions == 25 # Latest value kept
    assert merged2[0].comments == 18
    assert merged2[0].shares == 3
    assert merged2[0].posted_at == "2026-10-27T18:40:00Z" # Original posted_at preserved
    assert merged2[0].image_url == "https://scontent.xx.fbcdn.net/img.jpg" # Original image preserved
    assert merged2[0].scraped_at == "2026-10-29T04:00:00Z"
