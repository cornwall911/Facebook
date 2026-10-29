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

    p = Path(arg_value.strip().strip("'\""))
    if p.exists() and p.is_file():
        with open(p, "r", encoding="utf-8") as f:
            return [line.strip().strip("'\"") for line in f if line.strip() and not line.strip().startswith("#")]
    
    # Comma-separated
    return [item.strip().strip("'\"") for item in arg_value.split(",") if item.strip().strip("'\"")]

def main():
    parser = argparse.ArgumentParser(description="Facebook Viral Post Scout (Powered by Scrapling)")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run the scouting pipeline")
    run_parser.add_argument("-g", "--groups", help="Path to groups text file or comma-separated list of group IDs/URLs")
    run_parser.add_argument("-k", "--keywords", help="Optional keywords or path to keywords text file")
    run_parser.add_argument("-r", "--min-reactions", type=int, default=None, help="Minimum reactions threshold")
    run_parser.add_argument("--headless", action="store_true", default=None, help="Run browser in background headless mode")
    run_parser.add_argument("--no-headless", action="store_false", dest="headless", help="Run browser visibly on screen")
    run_parser.add_argument("-c", "--cookies", help="Path to cookies.json file")
    run_parser.add_argument("-o", "--output", help="Output directory for reports and images (default: data)")

    # Command: verify-login
    verify_parser = subparsers.add_parser("verify-login", help="Verify Facebook session status (logged-in / logged-out / checkpoint)")
    verify_parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")

    # Command: dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Rebuild the HTML dashboard from saved source posts")
    dash_parser.add_argument("-o", "--output", help="Output directory for reports (default: data)")

    args = parser.parse_args()

    if args.command == "verify-login":
        from fb_winner_scout.session import FacebookSession
        config = ScoutConfig.from_env()
        config.headless = True
        session = FacebookSession(config)
        context = session.start()
        page = context.new_page()
        status = session.check_session_status(page)
        print(f"\n[SESSION_STATUS]: {status}")
        session.close()
        sys.exit(0 if status == "logged-in" else 1)

    elif args.command in ("run", None):
        config = ScoutConfig.from_env()

        # Command line overrides
        if getattr(args, "min_reactions", None) is not None:
            config.min_reactions = args.min_reactions
        if getattr(args, "headless", None) is not None:
            config.headless = args.headless
        if getattr(args, "cookies", None):
            config.cookies_file = Path(args.cookies)
        if getattr(args, "output", None):
            config.output_dir = Path(args.output)

        groups = load_list_from_file_or_arg(getattr(args, "groups", None), "groups.txt")
        keywords = load_list_from_file_or_arg(getattr(args, "keywords", None), "keywords.txt")

        if not groups:
            print("[!] Error: No groups specified! Provide --groups <file_or_id> or create a 'groups.txt' file.")
            sys.exit(1)

        pipeline = ScoutPipeline(config)
        pipeline.run(groups, keywords)

    elif args.command == "dashboard":
        from fb_winner_scout.storage import StorageManager
        from fb_winner_scout.dashboard import generate_html_dashboard
        config = ScoutConfig.from_env()
        storage = StorageManager(config)
        posts = storage.load_source_posts()
        print(f"[*] Loaded {len(posts)} live source posts. Regenerating dashboard...")
        generate_html_dashboard(posts, config)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
