import time
import random
import urllib.parse
from typing import List, Set, Optional
from patchright.sync_api import Page, Locator
from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.parser import ScrapedPost, parse_count

class FacebookGroupCrawler:
    def __init__(self, page: Page, config: ScoutConfig):
        self.page = page
        self.config = config

    def search_group(self, group_id: str, keyword: str) -> List[ScrapedPost]:
        """
        Navigates to group search page, scrolls, and collects posts matching criteria.
        """
        clean_group = group_id.strip().rstrip("/").split("/")[-1]
        encoded_kw = urllib.parse.quote(keyword.strip())
        search_url = f"https://www.facebook.com/groups/{clean_group}/search/?q={encoded_kw}"

        print(f"\n[Crawler] Searching in group '{clean_group}' for keyword '{keyword}'...")
        print(f"[Crawler] URL: {search_url}")

        try:
            self.page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(random.uniform(3.0, 5.0))
        except Exception as e:
            print(f"[Crawler Error] Failed to load search URL: {e}")
            return []

        scraped_posts: List[ScrapedPost] = []
        seen_post_ids: Set[str] = set()

        scroll_count = 0
        no_new_posts_streak = 0

        while scroll_count < self.config.max_scrolls and len(scraped_posts) < self.config.max_posts_per_search:
            # Locate all post containers in the search feed
            post_locators = self._get_post_elements()
            new_found_in_batch = 0

            for post_loc in post_locators:
                try:
                    post_data = self._extract_post_data(post_loc, clean_group, keyword)
                    if not post_data:
                        continue

                    if post_data.post_id in seen_post_ids:
                        continue

                    seen_post_ids.add(post_data.post_id)
                    new_found_in_batch += 1

                    # Check viral threshold
                    if post_data.reactions_count >= self.config.min_reactions:
                        print(f"  [+] VIRAL POST FOUND: {post_data.reactions_count} reactions | {post_data.post_url}")
                        scraped_posts.append(post_data)
                    else:
                        print(f"  [-] Skipped post {post_data.post_id}: {post_data.reactions_count} reactions (< {self.config.min_reactions})")

                except Exception as ex:
                    # Skip post parsing errors gracefully
                    continue

            # Check termination
            if new_found_in_batch == 0:
                no_new_posts_streak += 1
                if no_new_posts_streak >= 3:
                    print("[Crawler] No more new posts loading. Ending search.")
                    break
            else:
                no_new_posts_streak = 0

            # Scroll down
            scroll_count += 1
            self._human_scroll()

        print(f"[Crawler] Finished search for '{keyword}' in '{clean_group}'. Total viral posts collected: {len(scraped_posts)}")
        return scraped_posts

    def _get_post_elements(self) -> List[Locator]:
        """Finds post containers on the Facebook search result page."""
        # Facebook uses div[role='feed'] or div[role='article'] or main containers
        selectors = [
            "div[role='feed'] > div",
            "div[role='article']",
            "div[data-pagelet*='FeedUnit']",
            "div[data-ad-preview='message']",
        ]
        for sel in selectors:
            locs = self.page.locator(sel)
            if locs.count() > 0:
                return [locs.nth(i) for i in range(locs.count())]
        return []

    def _extract_post_data(self, post: Locator, group_id: str, keyword: str) -> Optional[ScrapedPost]:
        """Extracts data from a single post locator."""
        # 1. Post Link & ID
        post_url, post_id = self._extract_permalink(post, group_id)
        if not post_id:
            return None

        # 2. Expand 'See more' if text is collapsed
        self._expand_text(post)

        # 3. Text / Caption
        caption = self._extract_caption(post)

        # 4. Reactions count
        reactions = self._extract_reactions(post)

        # 5. Comments & Shares
        comments, shares = self._extract_comments_and_shares(post)

        # 6. Author name
        author = self._extract_author(post)

        # 7. Images
        image_urls = self._extract_images(post)

        return ScrapedPost(
            post_id=post_id,
            post_url=post_url,
            keyword=keyword,
            group_id=group_id,
            author=author,
            caption=caption,
            reactions_count=reactions,
            comments_count=comments,
            shares_count=shares,
            image_urls=image_urls,
        )

    def _extract_permalink(self, post: Locator, group_id: str) -> tuple:
        """Finds the post permanent link and extracts its ID."""
        links = post.locator("a[href*='/posts/'], a[href*='/permalink/'], a[href*='multi_permalinks=']").all()
        for link in links:
            href = link.get_attribute("href") or ""
            if "/posts/" in href or "/permalink/" in href:
                # Clean query parameters
                base = href.split("?")[0]
                if not base.startswith("http"):
                    base = "https://www.facebook.com" + base
                # Extract post ID
                parts = [p for p in base.strip("/").split("/") if p]
                post_id = parts[-1] if parts else ""
                if post_id.isdigit():
                    return base, post_id
        
        # Fallback hash
        text_snippet = post.inner_text()[:40] if post.count() > 0 else ""
        if text_snippet:
            pseudo_id = str(abs(hash(text_snippet)))[:12]
            return f"https://www.facebook.com/groups/{group_id}", pseudo_id

        return "", ""

    def _expand_text(self, post: Locator):
        """Clicks 'See more' / 'عرض المزيد' buttons."""
        try:
            see_more_btns = post.locator(
                "div[role='button']:has-text('See more'), "
                "div[role='button']:has-text('See More'), "
                "div[role='button']:has-text('عرض المزيد')"
            )
            for i in range(min(see_more_btns.count(), 2)):
                see_more_btns.nth(i).click(timeout=1000)
                time.sleep(0.3)
        except Exception:
            pass

    def _extract_caption(self, post: Locator) -> str:
        """Extracts the message text of the post."""
        text_selectors = [
            "div[data-ad-preview='message']",
            "div[dir='auto'][style*='text-align']",
            "div[data-ad-comet-preview='message']",
            "div[role='article'] div[dir='auto']",
        ]
        for sel in text_selectors:
            loc = post.locator(sel)
            if loc.count() > 0:
                txt = loc.first.inner_text().strip()
                if len(txt) > 10:
                    return txt
        return ""

    def _extract_reactions(self, post: Locator) -> int:
        """Extracts total reaction count."""
        # Check aria-labels like '120 reactions', '250 people reacted', etc.
        selectors = [
            "span[aria-label*='reactions']",
            "span[aria-label*='reaction']",
            "span[aria-label*='تفاعل']",
            "span[aria-label*='معجب']",
            "span[role='toolbar']",
            "div[aria-label*='See who reacted']",
        ]
        for sel in selectors:
            loc = post.locator(sel)
            if loc.count() > 0:
                label = loc.first.get_attribute("aria-label") or loc.first.inner_text()
                cnt = parse_count(label)
                if cnt > 0:
                    return cnt

        # Check raw text near like icons / footer
        footer_spans = post.locator("span").all()
        for span in footer_spans[-15:]: # usually in the bottom area
            txt = span.inner_text().strip()
            if txt and (txt.isdigit() or any(k in txt for k in ["K", "k", "M", "ألف", "مليون"])):
                cnt = parse_count(txt)
                if cnt >= 20: # sensible threshold
                    return cnt

        return 0

    def _extract_comments_and_shares(self, post: Locator) -> tuple:
        """Extracts comment and share counts."""
        comments = 0
        shares = 0
        text = post.inner_text()
        
        # Look for e.g. "45 comments", "١٢ تعليقاً"
        import re
        c_match = re.search(r"([\d\.,kKألف]+)\s*(?:comments?|تعليق)", text, re.IGNORECASE)
        if c_match:
            comments = parse_count(c_match.group(1))

        s_match = re.search(r"([\d\.,kKألف]+)\s*(?:shares?|مشاركة)", text, re.IGNORECASE)
        if s_match:
            shares = parse_count(s_match.group(1))

        return comments, shares

    def _extract_author(self, post: Locator) -> str:
        """Extracts post author name."""
        try:
            author_loc = post.locator("h2 a, h3 a, strong a, a[role='link']").first
            if author_loc.count() > 0:
                return author_loc.inner_text().strip()
        except Exception:
            pass
        return ""

    def _extract_images(self, post: Locator) -> List[str]:
        """Extracts product / post image URLs."""
        image_urls = []
        try:
            imgs = post.locator("img").all()
            for img in imgs:
                src = img.get_attribute("src") or ""
                # Filter out small emojis, avatars, badges
                if "emoji.php" in src or "rsrc.php" in src:
                    continue
                
                # Check dimensions or scontent URL
                if "scontent" in src or "fbcdn" in src:
                    image_urls.append(src)
        except Exception:
            pass
        return image_urls

    def _human_scroll(self):
        """Scrolls with randomized steps and pauses to mimic human behavior."""
        scroll_y = random.randint(500, 900)
        self.page.evaluate(f"window.scrollBy({{top: {scroll_y}, behavior: 'smooth'}})")
        delay = random.uniform(self.config.scroll_delay_min, self.config.scroll_delay_max)
        time.sleep(delay)
