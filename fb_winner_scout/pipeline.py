import time
import random
from datetime import datetime, timezone
from typing import List
from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.session import FacebookSession
from fb_winner_scout.crawler import FacebookGroupCrawler
from fb_winner_scout.storage import StorageManager
from fb_winner_scout.parser import SourcePost
from fb_winner_scout.telegram_notifier import TelegramNotifier
from fb_winner_scout.dashboard import generate_html_dashboard

class ScoutPipeline:
    def __init__(self, config: ScoutConfig):
        self.config = config
        self.storage = StorageManager(config)
        self.notifier = TelegramNotifier()

    def run(self, groups: List[str], keywords: List[str] = None) -> List[SourcePost]:
        started_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print("\n" + "=" * 55)
        print("  🚀 Facebook Viral Post Scout (Live Pipeline)")
        print("=" * 55)
        print(f"[*] Started at: {started_at}")
        print(f"[*] Groups to search: {len(groups)}")
        print(f"[*] Output contract: public/source_posts.json & public/run_status.json")
        print("=" * 55 + "\n")

        session = FacebookSession(self.config)
        context = session.start()
        page = context.new_page()

        groups_stats = []
        errors = []
        all_new_posts: List[SourcePost] = []
        session_status = "logged-out"

        try:
            # 1. Verify Login Session
            print("[*] Verifying Facebook login session...")
            session_status = session.check_session_status(page)
            print(f"[*] Session Status: '{session_status}'")

            if session_status != "logged-in":
                err_msg = f"Facebook session is not logged in: status='{session_status}'. Run aborted."
                print(f"[!] CRITICAL: {err_msg}")
                errors.append(err_msg)
                self.notifier.notify_error(err_msg, "التحقق من جلسة فيسبوك")
                
                # Write run_status.json with failure reason and write NO posts
                finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                self.storage.save_run_status(
                    started_at=started_at,
                    finished_at=finished_at,
                    session=session_status,
                    groups=[],
                    total_written=0,
                    errors=errors,
                    data_source="live"
                )
                return []

            # 2. Iterate groups with human-like pacing
            crawler = FacebookGroupCrawler(page, self.config)

            for idx, g in enumerate(groups, 1):
                clean_g = g.strip()
                if not clean_g or clean_g.startswith("#"):
                    continue

                print(f"\n---> [{idx}/{len(groups)}] Processing Group: {clean_g}")
                # Prioritize top affiliate store sniffers to harvest 50+ posts with product links daily
                high_intent_affiliate = ["walmart", "amazon", "walmrt.us"]
                custom_terms = [k.strip() for k in (keywords or []) if k.strip() and not k.strip().startswith("#")]
                search_terms = [t for t in high_intent_affiliate if t not in custom_terms] + custom_terms
                search_terms = search_terms[:3]
                posts, g_stats = crawler.scrape_group(clean_g, max_scrolls=8, search_queries=search_terms if search_terms else None)
                groups_stats.append({
                    "group": g_stats["group"],
                    "ok": g_stats["ok"],
                    "posts_seen": g_stats["posts_seen"],
                    "posts_with_link": g_stats["posts_with_link"],
                    "error": g_stats["error"]
                })

                all_new_posts.extend(posts)

                if not g_stats["ok"]:
                    errors.append(f"Group {clean_g}: {g_stats['error']}")
                    # If checkpoint or block encountered, stop run immediately to avoid account harm
                    if g_stats["error"] and ("checkpoint" in g_stats["error"].lower() or "login" in g_stats["error"].lower()):
                        print("[!] Stopping pipeline immediately due to session checkpoint or block.")
                        session_status = "checkpoint"
                        break

                # Respectful inter-group delay (3 to 6 seconds)
                if idx < len(groups):
                    pause = random.uniform(3.0, 5.5)
                    print(f"[*] Pausing {pause:.1f}s before next group...")
                    time.sleep(pause)

            # 3. Save & Deduplicate into public/source_posts.json
            merged_posts = self.storage.merge_source_posts(all_new_posts)
            total_written = len(all_new_posts)

            # 4. Generate Dashboard from unified data (live source + catalog)
            try:
                unified_posts = self.storage.load_all_dashboard_posts()
                generate_html_dashboard(unified_posts, self.config)
            except Exception as e:
                print(f"[Dashboard Warning] Could not regenerate dashboard: {e}")

            finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            # 5. Write Contract C: public/run_status.json
            self.storage.save_run_status(
                started_at=started_at,
                finished_at=finished_at,
                session=session_status,
                groups=groups_stats,
                total_written=total_written,
                errors=errors,
                data_source="live"
            )

            print("\n" + "=" * 55)
            print(f"  🎉 RUN COMPLETE! Total new posts with links: {total_written} | Total in database: {len(merged_posts)}")
            print("=" * 55)

            return merged_posts

        except Exception as e:
            finished_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            err_str = f"Pipeline execution error: {e}"
            print(f"[Pipeline Error] {err_str}")
            errors.append(err_str)
            self.storage.save_run_status(
                started_at=started_at,
                finished_at=finished_at,
                session=session_status,
                groups=groups_stats,
                total_written=len(all_new_posts),
                errors=errors,
                data_source="live"
            )
            self.notifier.notify_error(str(e), "أثناء البحث في الجروبات")
            raise e

        finally:
            print("[*] Closing browser session...")
            session.close()
