import pytest
from unittest.mock import patch, MagicMock
from fb_winner_scout.post_copywriter import (
    build_copywriter_prompt,
    clean_generated_caption,
    PostCopywriter,
    generate_offline_caption
)
from fb_winner_scout.parser import ScrapedPost

def test_build_copywriter_prompt():
    post = ScrapedPost(
        post_id="12345",
        post_url="https://facebook.com/12345",
        keyword="rv gadget",
        group_id="rv_lovers",
        caption="Our camper shower was always leaking and making a mess until we installed this corner guard.",
        amazon_query="rv shower corner guard",
        is_product=True
    )
    prompt = build_copywriter_prompt(post)
    
    prompt_upper = prompt.upper()
    assert "BRAND BRAIN" in prompt_upper
    assert "PLAYBOOK" in prompt_upper
    assert "QUALITY GATE" in prompt_upper
    assert "SHORT" in prompt_upper
    assert "RV SHOWER CORNER GUARD" in prompt_upper
    assert "SHOWER WAS ALWAYS LEAKING" in prompt_upper

def test_clean_generated_caption():
    raw_output = """Here is the caption:
"Finally found an easy fix for leaking camper showers! Installed this $12 guard last weekend and it saved our bathroom floors. 

I'll drop the link in the first comment 👇"
"""
    cleaned = clean_generated_caption(raw_output)
    assert not cleaned.startswith("Here is the caption")
    assert not cleaned.startswith('"')
    assert "Finally found an easy fix" in cleaned
    assert "first comment" in cleaned

def test_offline_fallback():
    post = ScrapedPost(
        post_id="12345",
        post_url="https://facebook.com/12345",
        keyword="kitchen gadget",
        group_id="kitchen_finds",
        caption="Can anyone recommend a good vegetable chopper?",
        amazon_query="vegetable chopper",
        is_product=True
    )
    fallback = generate_offline_caption(post)
    assert len(fallback) > 10
    assert "link in the first comment" in fallback.lower()

def test_post_copywriter_without_api_key():
    copywriter = PostCopywriter(api_key=None)
    post = ScrapedPost(
        post_id="999",
        post_url="https://facebook.com/999",
        keyword="amazon finds",
        group_id="deals",
        caption="Best purchase this year!",
        is_product=True
    )
    caption = copywriter.generate_caption(post)
    assert isinstance(caption, str)
    assert len(caption) > 0

def test_gemini_api_mock_success():
    copywriter = PostCopywriter(api_key="fake-test-key")
    post = ScrapedPost(
        post_id="111",
        post_url="https://facebook.com/111",
        keyword="rv upgrade",
        group_id="rv",
        caption="Installed this new water pressure regulator.",
        amazon_query="water pressure regulator",
        is_product=True
    )
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({
        "candidates": [{
            "content": {
                "parts": [{"text": "If you own an RV, do NOT hook up to city water without one of these! Saved our plumbing.\n\nLink in first comment 👇"}]
            }
        }]
    }).encode("utf-8")

    with patch("urllib.request.urlopen", return_value=fake_response):
        caption = copywriter.generate_caption(post)
        assert "do NOT hook up to city water" in caption
        assert "Link in first comment" in caption

if __name__ == "__main__":
    test_build_copywriter_prompt()
    test_clean_generated_caption()
    test_offline_fallback()
    test_post_copywriter_without_api_key()
    print("All post copywriter tests passed successfully!")
