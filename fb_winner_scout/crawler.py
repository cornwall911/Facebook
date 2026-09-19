import time
import random
import urllib.parse
from typing import List, Set
from patchright.sync_api import Page
from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.parser import ScrapedPost, parse_count, extract_affiliate_link
from fb_winner_scout.product_classifier import classify_post_product

JS_EXTRACT_POSTS = r"""
() => {

    const results = [];
    
    // 1. Expand 'See more' / 'عرض المزيد'
    try {
        document.querySelectorAll("div[role='button']").forEach(b => {
            const t = b.innerText;
            if (t && (t === "See more" || t === "See More" || t.includes("عرض المزيد"))) {
                b.click();
            }
        });
    } catch(e) {}

    // 2. Locate feed articles
    const articles = document.querySelectorAll("div[role='feed'] > div, div[role='article'], div[data-pagelet*='FeedUnit']");

    articles.forEach(art => {
        let postUrl = "";
        let postId = "";
        const links = art.querySelectorAll("a[href*='/posts/'], a[href*='/permalink/'], a[href*='multi_permalinks=']");
        for (const l of links) {
            const h = l.getAttribute("href") || "";
            if (h.includes("/posts/") || h.includes("/permalink/")) {
                const base = h.split("?")[0];
                const parts = base.replace(/\/+$/, "").split("/").filter(Boolean);
                const last = parts[parts.length - 1];
                if (last && /^\d+$/.test(last)) {
                    postUrl = base.startsWith("http") ? base : "https://www.facebook.com" + base;
                    postId = last;
                    break;
                }
            }
        }

        const textSnippet = art.innerText ? art.innerText.substring(0, 60) : "";
        if (!postId && textSnippet && textSnippet.length > 15) {
            let hash = 0;
            for (let i = 0; i < textSnippet.length; i++) {
                hash = ((hash << 5) - hash) + textSnippet.charCodeAt(i);
                hash |= 0;
            }
            postId = String(Math.abs(hash)).substring(0, 12);
        }

        if (!postId) return;

        // Caption
        let caption = "";
        const msgEl = art.querySelector("div[data-ad-preview='message'], div[data-ad-comet-preview='message'], div[dir='auto'][style*='text-align']");
        if (msgEl) {
            caption = msgEl.innerText.trim();
        } else {
            const dirEls = art.querySelectorAll("div[dir='auto']");
            for (const d of dirEls) {
                const t = d.innerText.trim();
                if (t.length > 25 && !t.includes("Like") && !t.includes("Comment") && !t.includes("Share")) {
                    caption = t;
                    break;
                }
            }
        }

        // Reactions
        let reactionsRaw = "";
        const allWithAria = art.querySelectorAll("[aria-label]");
        for (const el of allWithAria) {
            const aria = el.getAttribute("aria-label") || "";
            const m = aria.match(/(?:أعجبني|تفاعل|like|reactions?|people)[:\s]+([٠-٩0-9.,kKmM]+)/i);
            if (m) {
                reactionsRaw = m[1];
                break;
            }
            const mPeople = aria.match(/([٠-٩0-9.,kKmM]+)\s*(?:شخص|أشخاص|people|person)/i);
            if (mPeople) {
                reactionsRaw = mPeople[1];
                break;
            }
        }

        if (!reactionsRaw) {
            const allElements = art.querySelectorAll("*");
            for (const el of allElements) {
                const t = el.innerText ? el.innerText.trim() : "";
                if (t.includes("كل التفاعلات") || t.includes("All reactions")) {
                    const mAll = t.match(/([٠-٩0-9.,kKmM]+)/);
                    if (mAll) {
                        reactionsRaw = mAll[1];
                        break;
                    }
                }
            }
        }

        if (!reactionsRaw) {
            const spans = art.querySelectorAll("span");
            for (let i = spans.length - 1; i >= Math.max(0, spans.length - 15); i--) {
                const txt = spans[i].innerText ? spans[i].innerText.trim() : "";
                if (txt && (/^[0-9]+([.,][0-9]+)?[kKmM]?$/.test(txt) || /^[٠-٩]+([٫،][٠-٩]+)?(ألف|مليون)?$/.test(txt))) {
                    reactionsRaw = txt;
                    break;
                }
            }
        }

        // Comments
        let commentsRaw = "";
        const allSpans = art.querySelectorAll("span, div[role='button']");
        for (const s of allSpans) {
            const txt = s.innerText ? s.innerText.trim() : "";
            const mCm = txt.match(/([٠-٩0-9.,kKmM]+)\s*(?:تعليق|تعليقًا|comments?)/i);
            if (mCm) {
                commentsRaw = mCm[1];
                break;
            }
        }

        // Shares
        let sharesRaw = "";
        for (const s of allSpans) {
            const txt = s.innerText ? s.innerText.trim() : "";
            const mSh = txt.match(/([٠-٩0-9.,kKmM]+)\s*(?:مشاركة|shares?)/i);
            if (mSh) {
                sharesRaw = mSh[1];
                break;
            }
        }

        // Author
        let author = "";
        const authorEl = art.querySelector("h2 a, h3 a, strong a, a[role='link']");
        if (authorEl) author = authorEl.innerText.trim();

        // Images
        const imgUrls = [];
        art.querySelectorAll("img").forEach(im => {
            const s = im.getAttribute("src") || "";
            if (s && !s.includes("emoji.php") && !s.includes("rsrc.php") && (s.includes("scontent") || s.includes("fbcdn"))) {
                imgUrls.push(s);
            }
        });

        results.push({
            post_id: postId,
            post_url: postUrl,
            caption: caption,
            reactions_raw: reactionsRaw,
            comments_raw: commentsRaw,
            shares_raw: sharesRaw,
            author: author,
            image_urls: imgUrls
        });
    });

    return results;
}
"""

class FacebookGroupCrawler:
    def __init__(self, page: Page, config: ScoutConfig):
        self.page = page
        self.config = config

    def search_group(self, group_id: str, keyword: str) -> List[ScrapedPost]:
        """
        Navigates to group search page (or global search if group_id is 'public'),
        scrolls, and collects posts matching criteria.
        """
        is_public = (group_id.strip().lower() in ("public", "facebook", "global", "all") or "search/posts" in group_id)
        encoded_kw = urllib.parse.quote(keyword.strip())
        
        if is_public:
            clean_group = "Public Search"
            search_url = f"https://www.facebook.com/search/posts/?q={encoded_kw}"
            print(f"\n[Crawler] 🌐 Searching Global Facebook Public Posts for '{keyword}'...")
        else:
            clean_group = group_id.strip().rstrip("/").split("/")[-1]
            if not keyword or keyword.strip().lower() in ("feed", "all", "none", ""):
                search_url = f"https://www.facebook.com/groups/{clean_group}/"
                print(f"\n[Crawler] 👥 Browsing main feed of group '{clean_group}'...")
            else:
                search_url = f"https://www.facebook.com/groups/{clean_group}/search/?q={encoded_kw}"
                print(f"\n[Crawler] 👥 Searching in group '{clean_group}' for keyword '{keyword}'...")

        print(f"[Crawler] URL: {search_url}")

        try:
            self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(2.5, 4.0))
        except Exception as e:
            print(f"[Crawler Error] Failed to load search URL: {e}")
            return []

        # Attempt to dismiss any initial login modal
        self._dismiss_modal_if_present()

        scraped_posts: List[ScrapedPost] = []
        seen_post_ids: Set[str] = set()

        scroll_count = 0
        no_new_posts_streak = 0

        while scroll_count < self.config.max_scrolls and len(scraped_posts) < self.config.max_posts_per_search:
            try:
                raw_batch = self.page.evaluate(JS_EXTRACT_POSTS)
            except Exception as e:
                print(f"[Crawler Warning] Fast extract evaluation failed: {e}")
                raw_batch = []

            new_found_in_batch = 0

            for raw in raw_batch:
                p_id = raw.get("post_id")
                if not p_id or p_id in seen_post_ids:
                    continue

                seen_post_ids.add(p_id)
                new_found_in_batch += 1

                rx_cnt = parse_count(raw.get("reactions_raw", ""))
                cm_cnt = parse_count(raw.get("comments_raw", ""))
                sh_cnt = parse_count(raw.get("shares_raw", ""))

                p_url = raw.get("post_url") or (f"https://www.facebook.com/groups/{clean_group}/posts/{p_id}" if not is_public else f"https://www.facebook.com/{p_id}")
                caption = raw.get("caption", "")
                img_urls = raw.get("image_urls", [])

                # Run physical product classifier
                is_prod, cat, amz_q, score = classify_post_product(caption, len(img_urls), keyword)

                # Physical winner criteria: Must have product photos
                if len(img_urls) == 0:
                    continue

                # Filter out obvious non-product exclusions (routes, complaints, chitchat)
                if not is_prod and "استبعاد" in cat:
                    continue

                # Extract direct product/affiliate link if present
                aff_url = extract_affiliate_link(caption)
                if aff_url:
                    is_prod = True
                    score = max(score, 90)

                # User requirement: Reactions 10+, or comments 10+, or fresh post with product photo & affiliate/high score
                is_fresh_winner = (len(img_urls) > 0) and (bool(aff_url) or score >= 65)
                is_qualified = (rx_cnt >= self.config.min_reactions) or (cm_cnt >= 10) or is_fresh_winner

                if is_qualified:
                    print(f"  [+] 📦 WINNING PRODUCT FOUND: {cat} (Score: {score}/100) | 👍 {rx_cnt} rx, 💬 {cm_cnt} cm | {p_url}")
                    scraped_posts.append(ScrapedPost(
                        post_id=p_id,
                        post_url=p_url,
                        keyword=keyword,
                        group_id=clean_group,
                        author=raw.get("author", ""),
                        caption=caption,
                        reactions_count=rx_cnt,
                        comments_count=cm_cnt,
                        shares_count=sh_cnt,
                        image_urls=img_urls,
                        is_product=is_prod,
                        product_category=cat,
                        amazon_query=amz_q,
                        winner_score=score,
                        affiliate_url=aff_url,
                    ))
                else:
                    if rx_cnt > 0:
                        print(f"  [-] Skipped post {p_id}: {rx_cnt} reactions (< {self.config.min_reactions})")

            # Check termination
            if new_found_in_batch == 0:
                no_new_posts_streak += 1
                if no_new_posts_streak >= 5:
                    break
            else:
                no_new_posts_streak = 0

            # Scroll down
            scroll_count += 1
            self._human_scroll()

        print(f"[Crawler] Finished search for '{keyword}' in '{clean_group}'. Total viral posts collected: {len(scraped_posts)}")
        return scraped_posts

    def _dismiss_modal_if_present(self):
        """Attempts to close or remove login blocker modal dialogs."""
        try:
            self.page.evaluate(r"""
            () => {
                const closeBtns = document.querySelectorAll("div[role='dialog'] div[role='button'], div[aria-label='إغلاق'], div[aria-label='Close']");
                for (const b of closeBtns) b.click();
            }
            """)
        except Exception:
            pass

    def _human_scroll(self):
        """Scrolls with randomized steps, mouse wheel, and container handling."""
        self._dismiss_modal_if_present()
        scroll_y = random.randint(800, 1400)
        try:
            # Physical mouse wheel on feed area
            self.page.mouse.move(600, 500)
            self.page.mouse.wheel(0, scroll_y)
        except Exception:
            pass

        try:
            # Fallback inner container scroll
            self.page.evaluate(r"""
            (dy) => {
                window.scrollBy({top: dy, behavior: 'smooth'});
                const all = document.querySelectorAll('*');
                for (const el of all) {
                    if (el.scrollHeight > el.clientHeight + 100 && el.clientHeight > 300) {
                        el.scrollTop += dy;
                    }
                }
            }
            """, scroll_y)
        except Exception:
            pass

        delay = random.uniform(self.config.scroll_delay_min, self.config.scroll_delay_max)
        time.sleep(delay)
