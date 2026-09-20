import time
from typing import List
from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.session import FacebookSession
from fb_winner_scout.crawler import FacebookGroupCrawler
from fb_winner_scout.storage import StorageManager
from fb_winner_scout.dashboard import generate_html_dashboard
from fb_winner_scout.parser import ScrapedPost
from fb_winner_scout.telegram_notifier import TelegramNotifier
from fb_winner_scout.post_copywriter import PostCopywriter

class ScoutPipeline:
    def __init__(self, config: ScoutConfig):
        self.config = config
        self.storage = StorageManager(config)
        self.notifier = TelegramNotifier()
        self.copywriter = PostCopywriter()

    def run(self, groups: List[str], keywords: List[str]) -> List[ScrapedPost]:
        print("\n" + "=" * 55)
        print("  🚀 Facebook Viral Post Scout (Powered by Scrapling)")
        print("=" * 55)
        print(f"[*] Groups to search: {len(groups)}")
        print(f"[*] Keywords: {len(keywords)}")
        print(f"[*] Min Reactions Threshold: {self.config.min_reactions}+")
        print(f"[*] Output directory: {self.config.output_dir.resolve()}")
        print("=" * 55 + "\n")

        # 1. Notify Telegram that run has started
        self.notifier.notify_run_started(
            groups_count=len(groups),
            keywords_count=len(keywords),
            min_reactions=self.config.min_reactions
        )

        session = FacebookSession(self.config)
        context = session.start()
        page = context.new_page()

        all_collected_posts: List[ScrapedPost] = []
        seen_post_ids = set()
        total_scanned_matches = 0
        initial_db_posts = self.storage.load_all_posts()
        initial_db_count = len(initial_db_posts)

        def add_post_safely(p: ScrapedPost):
            nonlocal total_scanned_matches
            total_scanned_matches += 1
            if p.post_id not in seen_post_ids:
                seen_post_ids.add(p.post_id)
                print(f"  [*] Downloading assets for post {p.post_id} ({len(p.image_urls)} images)...")
                self.storage.download_post_images(p)
                if p.is_product or p.winner_score > 0:
                    print(f"  [✍️] Generating short social caption for post {p.post_id}...")
                    p.generated_caption = self.copywriter.generate_caption(p)
                all_collected_posts.append(p)

        try:
            # 2. Verify Login
            print("[*] Verifying Facebook login...")
            logged_in = session.verify_login(page)
            if not logged_in:
                err_msg = "فشل التحقق من تسجيل الدخول في فيسبوك. يرجى تحديث الكوكيز cookies.json"
                print(f"[!] CRITICAL: {err_msg}")
                self.notifier.notify_error(err_msg, "التحقق من جلسة فيسبوك")

            # 3. Iterate groups & keywords
            for g_idx, group in enumerate(groups, 1):
                clean_group = group.strip()
                if not clean_group:
                    continue

                is_public = (clean_group.lower() in ("public", "facebook", "global", "all") or "search/posts" in clean_group)

                # 3a. In groups, browse the main group feed directly to capture all recent hot member posts
                if not is_public:
                    print(f"\n---> [{g_idx}/{len(groups)}] 📰 Browsing Main Feed of Group: '{clean_group}'...")
                    crawler = FacebookGroupCrawler(page, self.config)
                    feed_posts = crawler.search_group(clean_group, "")
                    for p in feed_posts:
                        add_post_safely(p)
                    time.sleep(2.0)

                # 3b. Search specific keywords
                for k_idx, kw in enumerate(keywords, 1):
                    clean_kw = kw.strip()
                    if not clean_kw:
                        continue

                    print(f"\n---> [{g_idx}/{len(groups)}] Group: {clean_group} | [{k_idx}/{len(keywords)}] Keyword: '{clean_kw}'")
                    
                    crawler = FacebookGroupCrawler(page, self.config)
                    posts = crawler.search_group(clean_group, clean_kw)

                    # Download images and generate high-converting post caption
                    for p in posts:
                        add_post_safely(p)

                    # Polite rest between searches
                    time.sleep(2.5)

            # 3c. Also scout Pinterest for top viral RV ideas and space savers
            try:
                from fb_winner_scout.pinterest_scout import PinterestScout
                print("\n" + "=" * 55)
                print("  📌 Scouting Pinterest for RV Space Savers & Gadgets...")
                print("=" * 55)
                pin_scout = PinterestScout(page, self.config)
                pin_posts = pin_scout.scout_all(max_per_query=8)
                for p in pin_posts:
                    add_post_safely(p)
            except Exception as e:
                print(f"[Warning] Pinterest scout step error: {e}")

            # 4. Export Results
            if all_collected_posts:
                print("\n" + "=" * 55)
                print(f"  🎉 SUCCESS! Collected {len(all_collected_posts)} unique viral posts.")
                print("=" * 55)
                excel_path = self.storage.save_to_excel(all_collected_posts)
                json_path = self.storage.save_to_json(all_collected_posts)
                all_accumulated = self.storage.load_all_posts()
                dash_path = generate_html_dashboard(all_accumulated, self.config)
                
                print(f"\n[+] Excel Report:   {excel_path.resolve()}")
                print(f"[+] JSON Database:  {json_path.resolve()}")
                print(f"[+] HTML Dashboard: {dash_path.resolve()}")
                print(f"[+] Images Folder:  {self.storage.images_dir.resolve()}\n")
            else:
                print(f"\n[!] No new posts reached the threshold ({self.config.min_reactions}+ reactions or 25+ comments) in this search.")
                all_accumulated = self.storage.load_all_posts()
                generate_html_dashboard(all_accumulated, self.config)

            # 5. Notify Telegram that run completed successfully
            top_rx = 0
            top_url = ""
            if all_collected_posts:
                sorted_p = sorted(all_collected_posts, key=lambda x: x.reactions_count, reverse=True)
                top_rx = sorted_p[0].reactions_count
                top_url = sorted_p[0].post_url

            new_unique = max(0, len(all_accumulated) - initial_db_count)
            self.notifier.notify_run_completed(
                new_unique_count=new_unique,
                total_unique_count=len(all_accumulated),
                scanned_count=total_scanned_matches,
                top_reactions=top_rx,
                top_post_url=top_url,
                total_groups=len(groups)
            )

        except Exception as e:
            print(f"[Pipeline Error] {e}")
            self.notifier.notify_error(str(e), "أثناء البحث في الجروبات")
            raise e

        finally:
            print("[*] Closing browser session...")
            session.close()

        return all_collected_posts

