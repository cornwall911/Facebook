from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.session import FacebookSession
from fb_winner_scout.parser import parse_count, extract_affiliate_link
from fb_winner_scout.product_classifier import classify_post_product
import time, json, urllib.parse, re

def harvest_watch_topics(page, topics):
    results = []
    seen_urls = set()

    for topic in topics:
        encoded = urllib.parse.quote(topic)
        url = f"https://www.facebook.com/watch/explore/{encoded}"
        print(f"\n[+] Exploring Watch Topic: '{topic}' ({url})")
        try:
            page.goto(url, timeout=25000)
            time.sleep(4)

            for scroll in range(4):
                page.mouse.wheel(0, 1500)
                time.sleep(2)

            cards = page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll("a[href*='/watch/'], a[href*='/reel/']"));
                return anchors.map(a => {
                    const h = a.href;
                    const container = a.closest("div[role='article']") || a.parentElement;
                    const text = (container ? container.innerText : a.innerText || '').substring(0, 300).replace(/\\n/g, ' ');
                    const img = a.querySelector('img') || (container ? container.querySelector('img') : null);
                    return {
                        url: h.split('?')[0],
                        text: text,
                        img: img ? img.src : ''
                    };
                }).filter(c => (c.url.includes('/reel/') || c.url.includes('/watch/?v=') || c.url.includes('/videos/')) && c.img);
            }""")

            for c in cards:
                u = c['url']
                if u not in seen_urls:
                    seen_urls.add(u)
                    results.append({
                        "post_url": u,
                        "source": f"Watch: {topic}",
                        "raw_text": c['text'],
                        "img": c['img'],
                        "topic": topic
                    })
            print(f"  Collected {len(cards)} items (Total unique so far: {len(results)})")
        except Exception as e:
            print(f"  Error on {topic}: {e}")

    return results

def main():
    cfg = ScoutConfig.from_env()
    session = FacebookSession(cfg)
    ctx = session.start()
    page = ctx.new_page()

    topics = [
        "rv gadgets",
        "rv must haves",
        "amazon rv finds",
        "camper gadgets",
        "rv kitchen gadgets",
        "rv organization",
        "rv upgrades",
        "rv camping hacks",
        "rv accessories"
    ]

    items = harvest_watch_topics(page, topics)
    print(f"\n==========================================")
    print(f"Total Unique Watch Videos Harvested: {len(items)}")
    print(f"==========================================")

    with open("data/reports/harvested_watch_items.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    session.browser.close()

if __name__ == "__main__":
    main()
