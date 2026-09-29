from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.session import FacebookSession
import time, json, re

target_media_urls = [
    ("Rv Camping Ideas & Hacking", "https://www.facebook.com/groups/1016323863626521/media/"),
    ("Cool RV Stuff - Gizmoz & Gadgets", "https://www.facebook.com/groups/825548446334240/media/"),
    ("RV Living & Storage ideas", "https://www.facebook.com/groups/466434735988069/media/"),
    ("RV Hacking Camping Ideas", "https://www.facebook.com/groups/RVhackcamp/media/"),
    ("RV Storage & Organization", "https://www.facebook.com/groups/1842777076228693/media/"),
    ("Keep Your Daydream", "https://www.facebook.com/KeepYourDaydream/photos/"),
    ("Mortons on the Move", "https://www.facebook.com/mortonsonthemove/photos/"),
    ("Camping World", "https://www.facebook.com/campingworld/photos/"),
    ("Go RVing", "https://www.facebook.com/gorving/photos/")
]

cfg = ScoutConfig.from_env()
session = FacebookSession(cfg)
ctx = session.start()
page = ctx.new_page()

all_photo_items = []
seen_post_ids = set()

for group_name, url in target_media_urls:
    print(f"\n[+] Scanning Media Tab: {group_name} ({url})")
    try:
        page.goto(url, timeout=30000)
        time.sleep(5)
        
        # Scroll 5 times to load dense photo grid
        for s in range(5):
            page.mouse.wheel(0, 1800)
            time.sleep(2)
            
        items = page.evaluate("""() => {
            const anchors = Array.from(document.querySelectorAll('a[href*="/photo/"], a[href*="fbid="]'));
            return anchors.map(a => {
                const img = a.querySelector('img');
                return {
                    href: a.href,
                    img: img ? img.src : '',
                    alt: img ? img.getAttribute('alt') || '' : ''
                };
            }).filter(x => x.img && x.img.includes('scontent'));
        }""")
        
        print(f"  Found {len(items)} photo elements in {group_name}")
        for it in items:
            h = it['href']
            # Match post ID from set=gm.<id> or set=pcb.<id> or set=a.<id>
            m = re.search(r'set=(?:gm|pcb|a)\.(\d+)', h)
            pid = m.group(1) if m else None
            
            # Or match from fbid
            if not pid:
                m_fb = re.search(r'fbid=(\d+)', h)
                pid = m_fb.group(1) if m_fb else None
                
            if pid and pid not in seen_post_ids:
                seen_post_ids.add(pid)
                
                # Construct direct post URL
                if "groups/" in url:
                    g_match = re.search(r'groups/([^/]+)', url)
                    gid = g_match.group(1) if g_match else ""
                    post_url = f"https://www.facebook.com/groups/{gid}/posts/{pid}/"
                else:
                    post_url = h.split('?')[0] if '?' in h else h

                all_photo_items.append({
                    "post_id": pid,
                    "post_url": post_url,
                    "photo_href": h,
                    "group_name": group_name,
                    "img": it['img'],
                    "alt": it['alt']
                })
        print(f"  Total unique posts so far: {len(all_photo_items)}")
    except Exception as e:
        print(f"  Error on {url}: {e}")

print(f"\n==========================================")
print(f"Total Unique Photo Posts Collected: {len(all_photo_items)}")
print(f"==========================================")

with open("data/reports/scanned_media_photos.json", "w", encoding="utf-8") as f:
    json.dump(all_photo_items, f, ensure_ascii=False, indent=2)

session.browser.close()
