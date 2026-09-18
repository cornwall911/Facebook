import time
import random
import urllib.parse
from typing import List, Set
from patchright.sync_api import Page
from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.parser import ScrapedPost, parse_count

JS_EXTRACT_POSTS = """
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
                const parts = base.replace(/\\/+$/, "").split("/").filter(Boolean);
                const last = parts[parts.length - 1];
                if (last && /^\\d+$/.test(last)) {
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

        // Reactions raw
        let reactionsRaw = "";
        const rxEl = art.querySelector("span[aria-label*='reaction'], span[aria-label*='reactions'], span[aria-label*='تفاعل'], span[aria-label*='معجب'], div[aria-label*='See who reacted']");
        if (rxEl) {
            reactionsRaw = rxEl.getAttribute("aria-label") || rxEl.innerText || "";
        }
        if (!reactionsRaw) {
            const spans = art.querySelectorAll("span");
            for (let i = spans.length - 1; i >= Math.max(0, spans.length - 15); i--) {
                const txt = spans[i].innerText.trim();
                if (txt && (/^\\d+([.,]\\d+)?[kKmM]?$/.test(txt) || /^[٠-٩]+([٫،][٠-٩]+)?(ألف|مليون)?$/.test(txt))) {
                    reactionsRaw = txt;
                    break;
                }
            }
        }

        // Comments & Shares
        let commentsRaw = "";
        let sharesRaw = "";
        const allSpans = art.querySelectorAll("span");
        for (const s of allSpans) {
            const txt = s.innerText.trim();
            if (txt.includes("comment") || txt.includes("تعليق")) commentsRaw = txt;
            if (txt.includes("share") || txt.includes("مشارك")) sharesRaw = txt;
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
        Navigates to group search page, scrolls, and collects posts matching criteria.
        Fast in-browser JavaScript extraction.
        """
        clean_group = group_id.strip().rstrip("/").split("/")[-1]
        encoded_kw = urllib.parse.quote(keyword.strip())
        search_url = f"https://www.facebook.com/groups/{clean_group}/search/?q={encoded_kw}"

        print(f"\n[Crawler] Searching in group '{clean_group}' for keyword '{keyword}'...")
        print(f"[Crawler] URL: {search_url}")

        try:
            self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(random.uniform(2.5, 4.0))
        except Exception as e:
            print(f"[Crawler Error] Failed to load search URL: {e}")
            return []

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

                p_url = raw.get("post_url") or f"https://www.facebook.com/groups/{clean_group}/posts/{p_id}"

                # Check viral threshold
                if rx_cnt >= self.config.min_reactions:
                    print(f"  [+] VIRAL POST FOUND: 👍 {rx_cnt} reactions | {p_url}")
                    scraped_posts.append(ScrapedPost(
                        post_id=p_id,
                        post_url=p_url,
                        keyword=keyword,
                        group_id=clean_group,
                        author=raw.get("author", ""),
                        caption=raw.get("caption", ""),
                        reactions_count=rx_cnt,
                        comments_count=cm_cnt,
                        shares_count=sh_cnt,
                        image_urls=raw.get("image_urls", []),
                    ))
                else:
                    if rx_cnt > 0:
                        print(f"  [-] Skipped post {p_id}: {rx_cnt} reactions (< {self.config.min_reactions})")

            # Check termination
            if new_found_in_batch == 0:
                no_new_posts_streak += 1
                if no_new_posts_streak >= 2:
                    break
            else:
                no_new_posts_streak = 0

            # Scroll down
            scroll_count += 1
            self._human_scroll()

        print(f"[Crawler] Finished search for '{keyword}' in '{clean_group}'. Total viral posts collected: {len(scraped_posts)}")
        return scraped_posts

    def _human_scroll(self):
        """Scrolls with randomized steps and pauses to mimic human behavior."""
        scroll_y = random.randint(600, 950)
        self.page.evaluate(f"window.scrollBy({{top: {scroll_y}, behavior: 'smooth'}})")
        delay = random.uniform(self.config.scroll_delay_min, self.config.scroll_delay_max)
        time.sleep(delay)
