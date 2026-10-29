import re
from pathlib import Path
import pytest
from scrapling.parser import Selector
from fb_winner_scout.parser import (
    extract_outbound_link,
    parse_count,
    parse_posted_at,
    SourcePost,
    parse_post_with_scrapling
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_scrapling_selector_extract_links():
    html = (FIXTURES_DIR / "post_with_link.html").read_text(encoding="utf-8")
    sel = Selector(html)
    
    # 1. Scrapling CSS extraction of links
    raw_links = sel.css("a::attr(href)").getall()
    assert len(raw_links) >= 2
    
    # Decode outbound link using our parser
    outbound = [extract_outbound_link(l) for l in raw_links if extract_outbound_link(l)]
    assert "https://walmrt.us/4eojgm9" in outbound

def test_scrapling_selector_extract_reactions_and_comments():
    html = (FIXTURES_DIR / "post_with_link.html").read_text(encoding="utf-8")
    sel = Selector(html)
    
    # Find aria labels
    aria_texts = sel.css("[aria-label]::attr(aria-label)").getall()
    like_aria = next((a for a in aria_texts if "Like:" in a or "reactions" in a), None)
    assert like_aria is not None
    assert parse_count(like_aria) == 11

    # Find comments and shares in text
    all_texts = [t.strip() for t in sel.css("span::text, div::text").getall() if t.strip()]
    comments_str = next((t for t in all_texts if re.search(r"\d+\s*comments?", t, re.I)), None)
    shares_str = next((t for t in all_texts if re.search(r"\d+\s*shares?", t, re.I)), None)
    
    assert parse_count(comments_str) == 16
    assert parse_count(shares_str) == 3

def test_scrapling_selector_k_reactions():
    html = (FIXTURES_DIR / "post_k_reactions.html").read_text(encoding="utf-8")
    sel = Selector(html)
    
    aria_texts = sel.css("[aria-label]::attr(aria-label)").getall()
    like_aria = next((a for a in aria_texts if "1.2K" in a), None)
    assert like_aria is not None
    assert parse_count(like_aria) == 1200

def test_parse_post_with_scrapling_success():
    html = (FIXTURES_DIR / "post_with_link.html").read_text(encoding="utf-8")
    post = parse_post_with_scrapling(html, group_slug="test_group", group_name="Test Group")
    
    assert post is not None
    assert post.post_id == "9999999999999999"
    assert post.product_url == "https://walmrt.us/4eojgm9"
    assert post.reactions == 11
    assert post.comments == 16
    assert post.shares == 3
    assert "bedroom" in post.caption

def test_parse_post_with_scrapling_no_link():
    html = (FIXTURES_DIR / "post_no_link.html").read_text(encoding="utf-8")
    post = parse_post_with_scrapling(html, group_slug="test_group")
    assert post is None
