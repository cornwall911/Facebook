import os
import re
import json
import urllib.request
import urllib.error
from typing import Optional
from fb_winner_scout.parser import ScrapedPost

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def build_copywriter_prompt(post: ScrapedPost) -> str:
    """
    Constructs a 3-layer prompt (Brand Brain, Playbook, Quality Gate)
    specifically designed for SHORT, high-converting social/Facebook posts.
    """
    product_name = post.amazon_query or post.keyword or "this gadget"
    original_caption = (post.caption or "").strip()[:500]

    return f"""You are a master social copywriter creating a short, high-converting Facebook post for a viral product.

### LAYER 1: BRAND BRAIN
- Persona: A genuine, savvy member of community groups (RV, camping, home organization, smart gadgets).
- Tone: Natural, authentic, conversational, peer-to-peer (like sharing an honest discovery with friends).
- Voice: First-person, honest, practical. NOT a corporate salesperson or robotic marketer.

### LAYER 2: THE PLAYBOOK (SHORT POST STRUCTURE)
- Structure:
  1. Line 1 (The Hook): A punchy, scroll-stopping opening line that makes people stop scrolling before clicking "See more".
  2. Lines 2-3 (Problem & Solution): 1 to 2 short sentences explaining the exact pain point it solved or why it's worth every penny.
  3. Final Line (Natural Social CTA): An organic CTA like "I left the link in the first comment 👇" or "Drop a comment if you want the link!".
- STRICT LENGTH CONSTRAINT:
  * Maximum 35 to 65 words total!
  * Keep it short, punchy, with line breaks between thoughts for mobile readability.
  * NO long paragraphs or walls of text.

### LAYER 3: QUALITY GATE (STRICT RULES)
- BANNED AI CLICHES: Do NOT use words like "revolutionary", "game-changer", "look no further", "in today's world", "must-have gadget", "delve", "elevate".
- Sound 100% human and casual.
- Return ONLY the exact text ready to copy-paste. No intro ("Here is the caption:"), no labels like [Hook], no quotes around the whole post.

---
PRODUCT CONTEXT:
- Target Product / Keyword: {product_name}
- Niche: {post.keyword}
- Original User Discussion / Complaint:
"{original_caption}"
---
"""

def clean_generated_caption(text: str) -> str:
    """Cleans up any intro text, enclosing quotes, or markdown artifacts."""
    if not text:
        return ""
    
    clean = text.strip()
    
    # Remove leading markdown headers or preambles like "Here is the caption:"
    clean = re.sub(r"^(?:Here (?:is|are)[^\n]*:?|Caption:?|Suggested post:?|Post:?)\s*", "", clean, flags=re.IGNORECASE).strip()
    
    # Remove surrounding double quotes
    if clean.startswith('"') and clean.endswith('"') and len(clean) > 2:
        clean = clean[1:-1].strip()
        
    # Remove labels like [Hook] or [CTA] if generated
    clean = re.sub(r"\[(?:Hook|Body|CTA|Call to Action|Visual|Line \d+)\]:?\s*", "", clean, flags=re.IGNORECASE)
    
    return clean

def generate_offline_caption(post: ScrapedPost) -> str:
    """Generates a high-quality heuristic fallback caption when no API key is set or on network failure."""
    target = post.amazon_query or post.keyword or "this find"
    return (
        f"Honestly didn't expect {target} to work this well, but it literally solved the problem on our last trip! "
        f"Best purchase I've made in a while.\n\n"
        f"I left the direct link in the first comment for anyone who needs it 👇"
    )

class PostCopywriter:
    """Manages AI-driven short post copywriting using Google Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3.6-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", model)

    def generate_caption(self, post: ScrapedPost) -> str:
        """
        Generates a short, high-converting social caption for a scraped post.
        Gracefully falls back to offline heuristic if API key is missing or fails.
        """
        if not self.api_key:
            return generate_offline_caption(post)

        prompt = build_copywriter_prompt(post)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7
            }
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts and "text" in parts[0]:
                        caption = clean_generated_caption(parts[0]["text"])
                        return caption
            
            # Fallback if no text in response
            return generate_offline_caption(post)

        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"[Copywriter Warning] Gemini API HTTP Error {e.code}: {err_body[:120]}")
            return generate_offline_caption(post)
        except Exception as e:
            print(f"[Copywriter Warning] Failed to generate caption via Gemini API: {e}")
            return generate_offline_caption(post)
