import time
from typing import List
from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.session import FacebookSession
from fb_winner_scout.crawler import FacebookGroupCrawler
from fb_winner_scout.storage import StorageManager
from fb_winner_scout.dashboard import generate_html_dashboard
from fb_winner_scout.parser import ScrapedPost
from fb_winner_scout.telegram_notifier import TelegramNotifier

class ScoutPipeline:
    def __init__(self, config: ScoutConfig):
        self.config = config
        self.storage = StorageManager(config)
        self.notifier = TelegramNotifier()

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

                for k_idx, kw in enumerate(keywords, 1):
                    clean_kw = kw.strip()
                    if not clean_kw:
                        continue

                    print(f"\n---> [{g_idx}/{len(groups)}] Group: {clean_group} | [{k_idx}/{len(keywords)}] Keyword: '{clean_kw}'")
                    
                    crawler = FacebookGroupCrawler(page, self.config)
                    posts = crawler.search_group(clean_group, clean_kw)

                    # Download images for each viral post
                    for p in posts:
                        print(f"  [*] Downloading assets for post {p.post_id} ({len(p.image_urls)} images)...")
                        self.storage.download_post_images(p)
                        all_collected_posts.append(p)

                    # Polite rest between searches
                    time.sleep(3.0)

            # 4. Export Results
            if all_collected_posts:
                print("\n" + "=" * 55)
                print(f"  🎉 SUCCESS! Collected {len(all_collected_posts)} viral posts.")
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

            self.notifier.notify_run_completed(
                collected_count=len(all_collected_posts),
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

