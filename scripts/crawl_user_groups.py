from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.session import FacebookSession
from fb_winner_scout.crawler import JS_EXTRACT_POSTS
import time, json, urllib.parse

cfg = ScoutConfig.from_env()
session = FacebookSession(cfg)
ctx = session.start()
page = ctx.new_page()

target_groups = [
    "https://www.facebook.com/groups/1016323863626521/",
    "https://www.facebook.com/groups/825548446334240/"
]

all_posts = []
seen_ids = set()

for g in target_groups:
    print(f"\n[+] Crawling group: {g}")
    try:
        page.goto(g, timeout=30000)
        time.sleep(5)
        
        for s in range(8):
            page.evaluate("""() => {
                const arts = document.querySelectorAll("div[role='article'], div[role='feed'] > div");
                if (arts.length > 0) arts[arts.length - 1].scrollIntoView();
            }""")
            time.sleep(3)
            
            items = page.evaluate(JS_EXTRACT_POSTS)
            for it in items:
                pu = it.get('post_url', '')
                pid = it.get('post_id', '')
                imgs = it.get('image_urls', [])
                cap = it.get('caption', '')
                if pid and pid not in seen_ids and imgs and len(cap) > 15:
                    seen_ids.add(pid)
                    it['source_group'] = g
                    all_posts.append(it)
            print(f"  Scroll {s+1}/8 | Unique collected so far: {len(all_posts)}")
    except Exception as e:
        print(f"Error crawling {g}: {e}")

print(f"\nTotal collected: {len(all_posts)}")
with open("data/reports/crawled_user_groups.json", "w", encoding="utf-8") as f:
    json.dump(all_posts, f, ensure_ascii=False, indent=2)

session.browser.close()
