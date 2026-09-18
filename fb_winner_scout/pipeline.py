import time
from typing import List
from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.session import FacebookSession
from fb_winner_scout.crawler import FacebookGroupCrawler
from fb_winner_scout.storage import StorageManager
from fb_winner_scout.dashboard import generate_html_dashboard
from fb_winner_scout.parser import ScrapedPost

class ScoutPipeline:
    def __init__(self, config: ScoutConfig):
        self.config = config
        self.storage = StorageManager(config)

    def run(self, groups: List[str], keywords: List[str]) -> List[ScrapedPost]:
        print("\n" + "=" * 55)
        print("  🚀 Facebook Viral Post Scout (Powered by Scrapling)")
        print("=" * 55)
        print(f"[*] Groups to search: {len(groups)}")
        print(f"[*] Keywords: {len(keywords)}")
        print(f"[*] Min Reactions Threshold: {self.config.min_reactions}+")
        print(f"[*] Output directory: {self.config.output_dir.resolve()}")
        print("=" * 55 + "\n")

        session = FacebookSession(self.config)
        context = session.start()
        page = context.new_page()

        all_collected_posts: List[ScrapedPost] = []

        try:
            # 1. Verify Login
            print("[*] Verifying Facebook login...")
            logged_in = session.verify_login(page)
            if not logged_in:
                print("[!] CRITICAL: Facebook session is not logged in or checkpoint encountered.")
                print("    Please ensure your cookies.json contains active session cookies.")
                # We continue anyway in case public search works or user wants to proceed

            # 2. Iterate groups & keywords
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

            # 3. Export Results
            if all_collected_posts:
                print("\n" + "=" * 55)
                print(f"  🎉 SUCCESS! Collected {len(all_collected_posts)} viral posts.")
                print("=" * 55)
                excel_path = self.storage.save_to_excel(all_collected_posts)
                json_path = self.storage.save_to_json(all_collected_posts)
                dash_path = generate_html_dashboard(all_collected_posts, self.config)
                
                print(f"\n[+] Excel Report:   {excel_path.resolve()}")
                print(f"[+] JSON Database:  {json_path.resolve()}")
                print(f"[+] HTML Dashboard: {dash_path.resolve()}")
                print(f"[+] Images Folder:  {self.storage.images_dir.resolve()}\n")
            else:
                print("\n[!] No posts reached the threshold (100+ reactions) in this run.")

        finally:
            print("[*] Closing browser session...")
            session.close()

        return all_collected_posts
