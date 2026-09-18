import argparse
import sys
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

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
