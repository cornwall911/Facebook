from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.session import FacebookSession
import json, time

def main():
    cfg = ScoutConfig.from_env()
    session = FacebookSession(cfg)
    ctx = session.start()
    page = ctx.new_page()

    with open('data/reports/viral_posts.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)

    results = []

    print(f"Testing all {len(posts)} posts for real live availability on Facebook...")
    for i, p in enumerate(posts):
        u = p.get('post_url', '')
        pid = p.get('post_id', '')
        aff = p.get('affiliate_url', '')
        
        # Check if search URL
        if '/search/' in u:
            results.append({
                'post_id': pid,
                'status': 'search_fallback',
                'url': u,
                'post': p
            })
            print(f"[{i+1}/{len(posts)}] {pid} -> SEARCH FALLBACK (Not direct)")
            continue

        try:
            resp = page.goto(u, timeout=12000)
            time.sleep(1.5)
            t = page.title()
            body = page.locator('body').inner_text()[:300].replace('\n', ' ')
            is_avail = ("isn't available" not in body and "غير متوفر" not in body and "This content" not in body and "Log in" not in t)
            
            status = 'live' if is_avail else 'dead'
            results.append({
                'post_id': pid,
                'status': status,
                'url': u,
                'title': t,
                'post': p
            })
            print(f"[{i+1}/{len(posts)}] {pid} -> {status.upper()} (Title: {t[:25]})")
        except Exception as e:
            results.append({
                'post_id': pid,
                'status': 'error',
                'url': u,
                'error': str(e),
                'post': p
            })
            print(f"[{i+1}/{len(posts)}] {pid} -> ERROR: {e}")

    session.browser.close()

    with open('data/reports/link_validation.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    live_count = sum(1 for r in results if r['status'] == 'live')
    dead_count = sum(1 for r in results if r['status'] == 'dead')
    search_count = sum(1 for r in results if r['status'] == 'search_fallback')
    print("\n--- VALIDATION SUMMARY ---")
    print(f"Total: {len(results)}")
    print(f"Live Direct Facebook Posts: {live_count}")
    print(f"Dead / Unavailable Posts: {dead_count}")
    print(f"Search Fallback URLs: {search_count}")

if __name__ == '__main__':
    main()
