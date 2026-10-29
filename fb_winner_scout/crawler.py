import time
import random
import re
import urllib.parse
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Set, Dict, Any
from patchright.sync_api import Page
from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.parser import (
    SourcePost,
    parse_count,
    parse_posted_at,
    extract_outbound_link,
    parse_post_with_scrapling,
)

JS_GET_CONTAINER_HTMLS = r"""
() => {
    // 1. Expand 'See more' on captions
    try {
        document.querySelectorAll("div[role='button']").forEach(b => {
            const t = (b.innerText || "").trim();
            if ((t === "See more" || t === "See More" || t === "عرض المزيد") &&
                !t.includes("تعليق") && !t.includes("رد") && !t.includes("comment") && !t.includes("repl")) {
                b.click();
            }
        });
    } catch(e) {}

    // 2. Dismiss any inadvertent dialogs
    try {
        document.querySelectorAll("div[role='dialog'] div[aria-label='Close'], div[role='dialog'] div[aria-label='إغلاق']").forEach(c => c.click());
    } catch(e) {}

    const feed = document.querySelector("div[role='feed']");
    const containers = feed ? Array.from(feed.children) : Array.from(document.querySelectorAll("div[role='article']"));
    return containers.map(c => c.outerHTML).filter(h => h && h.length > 50);
}
"""

JS_EXTRACT_FEED_POSTS = r"""
() => {
    try {
        document.querySelectorAll("div[role='button']").forEach(b => {
            const t = (b.innerText || "").trim();
            if ((t === "See more" || t === "See More" || t === "عرض المزيد") &&
                !t.includes("تعليق") && !t.includes("رد") && !t.includes("comment") && !t.includes("repl")) {
                b.click();
            }
        });
    } catch(e) {}

    try {
        document.querySelectorAll("div[role='dialog'] div[aria-label='Close'], div[role='dialog'] div[aria-label='إغلاق']").forEach(c => c.click());
    } catch(e) {}

    const results = [];
    const feed = document.querySelector("div[role='feed']");
    const containers = feed ? Array.from(feed.children) : Array.from(document.querySelectorAll("div[role='article']"));

    for (const art of containers) {
        const textSnippet = (art.innerText || "").trim();
        if (textSnippet.length < 20) continue;

        let postUrl = "";
        let postId = "";
        const links = art.querySelectorAll("a[href*='/posts/'], a[href*='/permalink/'], a[href*='multi_permalinks=']");
        for (const l of links) {
            const h = l.getAttribute("href") || "";
            const m = h.match(/\/posts\/(\d+)/) || h.match(/multi_permalinks=(\d+)/) || h.match(/\/permalink\/(\d+)/);
            if (m) {
                postId = m[1];
                let base = h.split("?")[0].replace(/\/+$/, "");
                postUrl = base.startsWith("http") ? base + "/" : "https://www.facebook.com" + base + "/";
                break;
            }
        }
        if (!postId) continue;

        let caption = "";
        const msgEl = art.querySelector("div[dir='auto'][style*='text-align'], div[data-ad-preview='message'], div[data-ad-comet-preview='message']");
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

        const outbound = [];
        art.querySelectorAll("a[href]").forEach(a => {
            let h = a.getAttribute("href") || "";
            if (h.includes("l.facebook.com/l.php") && h.includes("u=")) {
                const mU = h.match(/[?&]u=([^&]+)/);
                if (mU) {
                    try { h = decodeURIComponent(mU[1]); } catch(e) {}
                }
            }
            h = h.split("&rdid=")[0].split("?rdid=")[0];
            if (h.includes("?") && (h.includes("__cft__") || h.includes("__tn__"))) {
                h = h.split("?")[0];
            }
            if (h.startsWith("http")) {
                const lower = h.toLowerCase();
                if (!lower.includes("facebook.com") && !lower.includes("instagram.com") && !lower.includes("fb.me") && !lower.includes("meta.com") && !lower.includes("threads.net")) {
                    outbound.push(h);
                }
            }
        });

        if (caption) {
            const mUrls = caption.match(/https?:\/\/[^\s\)"'>]+/g) || [];
            for (let cu of mUrls) {
                cu = cu.replace(/[.,;)>"']+$/, "");
                const cl = cu.toLowerCase();
                if (!cl.includes("facebook.com") && !cl.includes("instagram.com") && !cl.includes("fb.me") && !cl.includes("meta.com") && !cl.includes("threads.net")) {
                    outbound.push(cu);
                }
            }
        }

        let reactionsRaw = null;
        const rxEl = art.querySelector("div[aria-label*='Like:'], div[aria-label*='like:'], div[aria-label*='reactions']");
        if (rxEl) reactionsRaw = rxEl.getAttribute("aria-label");
        if (!reactionsRaw) {
            const tb = art.querySelector("span[role='toolbar']");
            if (tb && tb.parentElement) reactionsRaw = tb.parentElement.innerText;
        }

        let commentsRaw = null;
        let sharesRaw = null;
        art.querySelectorAll("span, div").forEach(el => {
            const t = (el.innerText || "").trim();
            const mC = t.match(/^([\d\.,kKmM]+)\s*comments?$/i);
            if (mC && !commentsRaw) commentsRaw = mC[1];
            const mS = t.match(/^([\d\.,kKmM]+)\s*shares?$/i);
            if (mS && !sharesRaw) sharesRaw = mS[1];
        });

        let postedAtRaw = null;
        for (const a of art.querySelectorAll("a[href*='/posts/'], a[href*='/permalink/']")) {
            const t = (a.innerText || "").trim();
            if (t && (/^\d+[hmwd]$/.test(t) || t.includes("ago") || t.includes("Yesterday") || /\d{4}/.test(t))) {
                postedAtRaw = t;
                break;
            }
            const aria = a.getAttribute("aria-label") || "";
            if (aria && (aria.includes("ago") || aria.includes("Yesterday") || /\d{4}/.test(aria))) {
                postedAtRaw = aria;
                break;
            }
        }

        let imageUrl = null;
        const imEl = art.querySelector("img[src*='scontent'], img[src*='fbcdn']");
        if (imEl) imageUrl = imEl.getAttribute("src");

        results.push({
            post_id: postId,
            post_url: postUrl,
            caption: caption,
            outbound_links: Array.from(new Set(outbound)),
            reactions_raw: reactionsRaw,
            comments_raw: commentsRaw,
            shares_raw: sharesRaw,
            posted_at_raw: postedAtRaw,
            image_url: imageUrl
        });
    }

    return results;
}
"""

def clean_group_target(group_target: str) -> Tuple[str, str]:
    """
    Cleans group target string and returns (group_slug, group_url).
    Strips trailing slashes, surrounding quotes, and extracts group id or slug.
    """
    s = group_target.strip().strip("'\"").rstrip("/")
    if "/groups/" in s:
        slug = s.split("/groups/")[-1].split("/")[0].split("?")[0]
    else:
        slug = s.split("/")[-1].split("?")[0]
    canonical_url = f"https://www.facebook.com/groups/{slug}/"
    return slug, canonical_url

class FacebookGroupCrawler:
    def __init__(self, page: Page, config: ScoutConfig):
        self.page = page
        self.config = config

    def _extract_posts_from_current_view(
        self,
        group_slug: str,
        group_name: str,
        seen_post_ids: Set[str]
    ) -> Tuple[List[SourcePost], int]:
        """
        Extracts posts using Scrapling's Selector with high fidelity,
        falling back to JS evaluation for any missed items.
        """
        extracted_posts: List[SourcePost] = []
        raw_seen_count = 0

        # Method 1: Scrapling Selector over outerHTML snapshots
        try:
            container_htmls = self.page.evaluate(JS_GET_CONTAINER_HTMLS)
        except Exception as e:
            print(f"[Crawler Warning] Container HTML extraction error: {e}")
            container_htmls = []

        scrapling_found = 0
        for html in container_htmls:
            raw_seen_count += 1
            sp = parse_post_with_scrapling(html, group_slug=group_slug, group_name=group_name)
            if sp and sp.post_id and sp.post_id not in seen_post_ids:
                seen_post_ids.add(sp.post_id)
                extracted_posts.append(sp)
                scrapling_found += 1
                print(f"  [+] 🦅 Scrapling Post {sp.post_id} | rx: {sp.reactions} | cm: {sp.comments} | link: {sp.product_url}")

        # Method 2: Fallback to JS extraction if Scrapling found 0 items or for extra resilience
        if scrapling_found == 0:
            try:
                raw_items = self.page.evaluate(JS_EXTRACT_FEED_POSTS)
            except Exception:
                raw_items = []

            for item in raw_items:
                pid = str(item.get("post_id", "")).strip()
                if not pid or pid in seen_post_ids:
                    continue

                outbound = item.get("outbound_links", [])
                product_url = None
                for u in outbound:
                    clean_u = extract_outbound_link(u)
                    if clean_u:
                        product_url = clean_u
                        break

                if not product_url:
                    continue

                seen_post_ids.add(pid)
                rx = parse_count(item.get("reactions_raw"))
                cm = parse_count(item.get("comments_raw"))
                sh = parse_count(item.get("shares_raw"))
                posted_at = parse_posted_at(item.get("posted_at_raw"))
                img_url = item.get("image_url")
                post_url = item.get("post_url") or f"https://www.facebook.com/groups/{group_slug}/posts/{pid}/"
                caption = (item.get("caption") or "").strip()

                sp = SourcePost(
                    post_id=pid,
                    post_url=post_url,
                    group=group_slug,
                    group_name=group_name,
                    caption=caption,
                    product_url=product_url,
                    reactions=rx,
                    comments=cm,
                    shares=sh,
                    posted_at=posted_at,
                    image_url=img_url,
                    scraped_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    data_source="live"
                )
                extracted_posts.append(sp)
                print(f"  [+] 🔗 Source Post {pid} | rx: {rx} | cm: {cm} | link: {product_url}")

        return extracted_posts, raw_seen_count

    def scrape_group(
        self,
        group_target: str,
        max_scrolls: int = 15,
        search_queries: Optional[List[str]] = None
    ) -> Tuple[List[SourcePost], Dict[str, Any]]:
        """
        Navigates to the group, scrolls aggressively, extracts posts with Scrapling,
        and optionally executes high-intent in-group searches for product finds.
        """
        group_slug, group_url = clean_group_target(group_target)
        stats = {
            "group": group_slug,
            "group_url": group_url,
            "ok": True,
            "posts_seen": 0,
            "posts_with_link": 0,
            "error": None
        }

        print(f"\n[Crawler] 👥 Navigating to group: {group_url}...")
        try:
            self.page.goto(group_url, wait_until="domcontentloaded", timeout=35000)
            time.sleep(random.uniform(2.5, 4.0))
        except Exception as e:
            err = f"Failed to load group URL: {e}"
            print(f"[Crawler Error] {err}")
            stats["ok"] = False
            stats["error"] = err
            return [], stats

        # Verify session status
        current_url = self.page.url.lower()
        if "checkpoint" in current_url:
            err = "Checkpoint encountered on group navigation"
            print(f"[Crawler Error] {err}")
            stats["ok"] = False
            stats["error"] = err
            return [], stats

        if "login" in current_url:
            err = "Redirected to login on group navigation"
            print(f"[Crawler Error] {err}")
            stats["ok"] = False
            stats["error"] = err
            return [], stats

        # Extract group name
        group_name = group_slug
        try:
            title_text = self.page.title()
            if "|" in title_text:
                group_name = title_text.split("|")[0].strip()
            elif " - " in title_text:
                group_name = title_text.split(" - ")[0].strip()
            elif title_text:
                group_name = title_text.strip()
        except Exception:
            pass

        seen_post_ids: Set[str] = set()
        source_posts: List[SourcePost] = []

        # -------------------------------------------------------------
        # Phase 1: Main Group Feed Fierce Scroll
        # -------------------------------------------------------------
        scroll_count = 0
        no_new_streak = 0

        while scroll_count < max_scrolls:
            new_posts, seen_count = self._extract_posts_from_current_view(
                group_slug, group_name, seen_post_ids
            )
            stats["posts_seen"] += seen_count
            stats["posts_with_link"] += len(new_posts)
            source_posts.extend(new_posts)

            if len(new_posts) == 0:
                no_new_streak += 1
                if no_new_streak >= 3 and scroll_count >= 4:
                    break
            else:
                no_new_streak = 0

            scroll_count += 1
            self._fierce_scroll()

        # Stay on the native group feed to completely avoid Facebook's /search/?q= login wall

        print(f"[Crawler] Completed group '{group_name}' ({group_slug}): seen {stats['posts_seen']} posts, {stats['posts_with_link']} with outbound product link.")
        return source_posts, stats

    def scrape_group_search(
        self,
        group_slug: str,
        group_name: str,
        query: str,
        max_scrolls: int = 4,
        seen_post_ids: Optional[Set[str]] = None
    ) -> List[SourcePost]:
        """
        Executes a targeted keyword search inside the Facebook group:
        https://www.facebook.com/groups/<group>/search/?q=<query>
        This directly finds posts sharing specific affiliate stores or gadgets.
        """
        if seen_post_ids is None:
            seen_post_ids = set()

        search_url = f"https://www.facebook.com/groups/{group_slug}/search/?q={urllib.parse.quote(query)}"
        print(f"  [+] 🔍 Running targeted in-group search: '{query}' ({search_url})...")

        try:
            self.page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
            time.sleep(random.uniform(2.5, 4.0))
        except Exception as e:
            print(f"  [!] In-group search load warning: {e}")
            return []

        search_posts: List[SourcePost] = []
        for s_idx in range(max_scrolls):
            new_posts, _ = self._extract_posts_from_current_view(
                group_slug, group_name, seen_post_ids
            )
            search_posts.extend(new_posts)
            self._fierce_scroll()

        print(f"  [+] 🔍 Finished in-group search '{query}': found {len(search_posts)} product posts.")
        return search_posts

    def _fierce_scroll(self):
        """
        Aggressive human-like scroll:
        1. Scrolls the last article directly into view (triggers Facebook virtual feed intersection observers).
        2. Sends PageDown key press.
        3. Simulates natural mouse wheel with jitter.
        """
        try:
            self.page.evaluate(r"""() => {
                const arts = document.querySelectorAll("div[role='feed'] > div, div[role='article']");
                if (arts.length > 0) {
                    arts[arts.length - 1].scrollIntoView({ behavior: 'smooth', block: 'end' });
                }
            }""")
        except Exception:
            pass

        try:
            self.page.keyboard.press("PageDown")
        except Exception:
            pass

        scroll_y = random.randint(850, 1500)
        try:
            self.page.mouse.wheel(0, scroll_y)
        except Exception:
            pass

        delay = random.uniform(self.config.scroll_delay_min, self.config.scroll_delay_max)
        time.sleep(delay)