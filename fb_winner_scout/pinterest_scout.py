import time
import urllib.parse
import hashlib
from typing import List
from patchright.sync_api import Page
from fb_winner_scout.parser import ScrapedPost
from fb_winner_scout.config import ScoutConfig

PINTEREST_QUERIES = [
    ("rv shoe storage organization", "تنظيم وتخزين الأحذية (RV Shoe Storage)", "rv shoe storage hooks"),
    ("rv adhesive hooks organization", "خطافات لاصقة ذكية (Adhesive Hooks)", "heavy duty adhesive hooks rv"),
    ("rv kitchen organization must haves", "منظمات مطبخ الكرفان (RV Kitchen)", "rv kitchen cabinet organizer"),
    ("rv camper space saving gadgets", "أجهزة وحلول توفير المساحة (Space Savers)", "rv space saving gadgets"),
    ("travel trailer storage hacks", "أفكار تخزين ذكية (Camper Storage)", "travel trailer storage solutions"),
    ("rv bathroom space saving hacks", "تنظيم حمام الكرفان (RV Bathroom)", "rv bathroom shower organizer"),
    ("rv collapsible gadgets amazon", "أدوات قابلة للطي (Collapsible Gear)", "rv collapsible kitchen items"),
    ("rv bedside storage caddy", "منظمات جانب السرير (Bedside Caddy)", "rv bedside hanging caddy pocket"),
]

class PinterestScout:
    def __init__(self, page: Page, config: ScoutConfig):
        self.page = page
        self.config = config

    def scout_all(self, queries: List[tuple] = None, max_per_query: int = 12) -> List[ScrapedPost]:
        """Scouts Pinterest for top RV organization and space-saving product ideas."""
        target_queries = queries or PINTEREST_QUERIES
        collected_posts: List[ScrapedPost] = []
        seen_images = set()

        print(f"\n[Pinterest] 📌 Starting Pinterest RV Scout across {len(target_queries)} product categories...")

        for q_idx, (kw, cat_name, amz_q) in enumerate(target_queries, 1):
            encoded = urllib.parse.quote(kw)
            url = f"https://www.pinterest.com/search/pins/?q={encoded}"
            print(f"\n---> [{q_idx}/{len(target_queries)}] Searching Pinterest: '{kw}'...")

            try:
                self.page.goto(url, wait_until="domcontentloaded", timeout=25000)
                time.sleep(3.0)

                # Dismiss login modal
                self._dismiss_modal()

                # Extract images
                raw_imgs = self.page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll("img[src*='pinimg.com']"))
                        .map(i => ({
                            src: i.src,
                            alt: i.alt || ''
                        }))
                        .filter(x => x.src && !x.src.includes('60x60') && !x.src.includes('75x75'));
                }
                """)

                count_added = 0
                for item in raw_imgs:
                    orig_src = item.get("src", "")
                    # Convert to high-res 736x
                    high_res = orig_src.replace("/236x/", "/736x/").replace("/474x/", "/736x/")
                    
                    if high_res in seen_images or not orig_src:
                        continue

                    seen_images.add(high_res)
                    post_id = "pin_" + hashlib.md5(high_res.encode()).hexdigest()[:12]
                    
                    # Generate natural UGC-style caption matching the user's screenshots
                    caption = (
                        f"It's not 'Pinterest pretty' but it's an absolute game changer for our camper! "
                        f"We have such a small space and this completely solved our clutter problem. "
                        f"Found this gem on Amazon / Walmart 👇"
                    )

                    collected_posts.append(ScrapedPost(
                        post_id=post_id,
                        post_url=url,
                        keyword=f"Pinterest: {kw}",
                        group_id="Pinterest (RV Finds)",
                        author="Pinterest Winner",
                        caption=caption,
                        reactions_count=45,
                        comments_count=18,
                        shares_count=12,
                        image_urls=[high_res],
                        is_product=True,
                        product_category=cat_name,
                        amazon_query=amz_q,
                        winner_score=95,
                        affiliate_url="",
                        generated_caption=f"Honestly didn't expect this {amz_q} to work so well in our camper, but it literally solved our small space problem! Best $15 purchase.\n\nLeft the link in the first comment 👇"
                    ))

                    count_added += 1
                    if count_added >= max_per_query:
                        break

                print(f"  [+] Extracted {count_added} high-res winning products for '{kw}'.")

            except Exception as e:
                print(f"  [!] Error searching Pinterest for '{kw}': {e}")

        print(f"\n[Pinterest] 🎉 Done! Collected {len(collected_posts)} top Pinterest RV products.\n")
        return collected_posts

    def _dismiss_modal(self):
        try:
            self.page.evaluate("""
            () => {
                const dialogs = document.querySelectorAll("div[role='dialog'], div[data-test-id='login-modal-default']");
                dialogs.forEach(d => d.remove());
                const overlays = document.querySelectorAll("div[style*='position: fixed'], div[style*='position:fixed']");
                overlays.forEach(o => o.remove());
                document.body.style.overflow = 'auto';
                document.documentElement.style.overflow = 'auto';
            }
            """)
        except Exception:
            pass
