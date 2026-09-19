import argparse
import sys
import time
from pathlib import Path
from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.pipeline import ScoutPipeline

def load_list_from_file_or_arg(arg_value: str, default_file: str) -> list:
    """Helper to parse a file or comma-separated list."""
    if not arg_value and Path(default_file).exists():
        arg_value = default_file

    if not arg_value:
        return []

    p = Path(arg_value)
    if p.exists() and p.is_file():
        with open(p, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    return [item.strip() for item in arg_value.split(",") if item.strip()]

def main():
    parser = argparse.ArgumentParser(description="Facebook Viral Post Scout (Powered by Scrapling)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run the scouting pipeline")
    run_parser.add_argument("-g", "--groups", help="Path to groups text file or comma-separated list of group IDs/URLs")
    run_parser.add_argument("-k", "--keywords", help="Path to keywords text file or comma-separated list of keywords")
    run_parser.add_argument("-r", "--min-reactions", type=int, default=None, help="Minimum reactions threshold (default: 100)")
    run_parser.add_argument("--headless", action="store_true", default=None, help="Run browser in background headless mode")
    run_parser.add_argument("--no-headless", action="store_false", dest="headless", help="Run browser visibly on screen")
    run_parser.add_argument("-c", "--cookies", help="Path to cookies.json file")
    run_parser.add_argument("-o", "--output", help="Output directory for reports and images (default: data)")

    # Command: dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Rebuild the HTML dashboard from saved posts")
    dash_parser.add_argument("-o", "--output", help="Output directory for reports (default: data)")

    # Command: generate-captions
    captions_parser = subparsers.add_parser("generate-captions", help="Generate AI short captions for existing saved winner posts")
    captions_parser.add_argument("--force", action="store_true", help="Regenerate captions even if they already exist")
    captions_parser.add_argument("-o", "--output", help="Output directory for reports (default: data)")

    # Command: pinterest
    pin_parser = subparsers.add_parser("pinterest", help="Scout Pinterest for RV organization and space-saving product ideas")
    pin_parser.add_argument("-o", "--output", help="Output directory for reports (default: data)")
    pin_parser.add_argument("--max-per-query", type=int, default=12, help="Max pins per category (default: 12)")

    args = parser.parse_args()

    if args.command in ("run", None):
        config = ScoutConfig.from_env()

        # Command line overrides
        if args.min_reactions is not None:
            config.min_reactions = args.min_reactions
        if args.headless is not None:
            config.headless = args.headless
        if args.cookies:
            config.cookies_file = Path(args.cookies)
        if args.output:
            config.output_dir = Path(args.output)

        groups = load_list_from_file_or_arg(getattr(args, "groups", None), "groups.txt")
        keywords = load_list_from_file_or_arg(getattr(args, "keywords", None), "keywords.txt")

        if not groups:
            print("[!] Error: No groups specified! Provide --groups <file_or_id> or create a 'groups.txt' file.")
            sys.exit(1)

        if not keywords:
            print("[!] Error: No keywords specified! Provide --keywords <file_or_kw> or create a 'keywords.txt' file.")
            sys.exit(1)

        pipeline = ScoutPipeline(config)
        pipeline.run(groups, keywords)

    elif args.command == "dashboard":
        from fb_winner_scout.storage import StorageManager
        from fb_winner_scout.dashboard import generate_html_dashboard
        config = ScoutConfig.from_env()
        if args.output:
            config.output_dir = Path(args.output)
        storage = StorageManager(config)
        posts = storage.load_all_posts()
        print(f"[*] Loaded {len(posts)} posts. Regenerating dashboard...")
        generate_html_dashboard(posts, config)

    elif args.command == "generate-captions":
        from fb_winner_scout.storage import StorageManager
        from fb_winner_scout.dashboard import generate_html_dashboard
        from fb_winner_scout.post_copywriter import PostCopywriter
        config = ScoutConfig.from_env()
        if args.output:
            config.output_dir = Path(args.output)
        storage = StorageManager(config)
        posts = storage.load_all_posts()
        copywriter = PostCopywriter()

        updated_count = 0
        for p in posts:
            if (p.is_product or p.winner_score > 0) and (not p.generated_caption or getattr(args, "force", False)):
                print(f"[*] Generating short caption for post {p.post_id} ({p.keyword})...")
                p.generated_caption = copywriter.generate_caption(p)
                updated_count += 1
                time.sleep(2.0)

        if updated_count > 0:
            storage.save_to_json(posts)
            storage.save_to_excel(posts)
            generate_html_dashboard(posts, config)
            print(f"[+] Successfully generated captions for {updated_count} winner posts and updated dashboard!")
        else:
            print("[*] No winner posts needed caption generation (all have captions or none qualified). Use --force to regenerate.")

    elif args.command == "pinterest":
        from patchright.sync_api import sync_playwright
        from fb_winner_scout.storage import StorageManager
        from fb_winner_scout.dashboard import generate_html_dashboard
        from fb_winner_scout.pinterest_scout import PinterestScout
        config = ScoutConfig.from_env()
        if args.output:
            config.output_dir = Path(args.output)
        storage = StorageManager(config)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            scout = PinterestScout(page, config)
            pin_posts = scout.scout_all(max_per_query=getattr(args, "max_per_query", 12))
            browser.close()

        for post in pin_posts:
            storage.download_post_images(post)

        storage.save_to_json(pin_posts)
        storage.save_to_excel(pin_posts)
        all_posts = storage.load_all_posts()
        generate_html_dashboard(all_posts, config)
        print(f"\n[+] 🎉 Successfully collected {len(pin_posts)} Pinterest RV product winners! Total in database: {len(all_posts)}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
