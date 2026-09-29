from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.session import FacebookSession
from fb_winner_scout.parser import extract_affiliate_link, parse_count
import time, json, re

urls = [
    "https://www.facebook.com/groups/466434735988069/posts/1074194491878754/",
    "https://www.facebook.com/groups/466434735988069/posts/1075323891765814/",
    "https://www.facebook.com/groups/466434735988069/posts/1074562088508661/",
    "https://www.facebook.com/groups/466434735988069/posts/1077491171549086",
    "https://www.facebook.com/groups/466434735988069/posts/1073739171924286/",
    "https://www.facebook.com/groups/466434735988069/posts/1079251458039724/",
    "https://www.facebook.com/groups/466434735988069/?multi_permalinks=1081400597824810&hoisted_section_header_type=recently_seen",
    "https://www.facebook.com/share/p/1GbD5k41TX/",
    "https://www.facebook.com/share/p/19R6Nv7QES/",
    "https://www.facebook.com/share/p/17cXZMA3Gh/",
    "https://www.facebook.com/share/p/19MK7AoexM/",
    "https://www.facebook.com/share/p/19J7RD9BpV/",
    "https://www.facebook.com/share/p/1FVRUNtory/",
    "https://www.facebook.com/share/p/1NE9khFFwE/",
    "https://www.facebook.com/share/p/18ZgTXZVgE/",
    "https://www.facebook.com/share/p/19UZGt32yu/",
    "https://www.facebook.com/share/p/1EoRHUz749/",
    "https://www.facebook.com/share/p/1DXGph2EfA/",
    "https://www.facebook.com/share/p/1DoWqJEh3p/",
    "https://www.facebook.com/share/p/1Dowj2gRSJ/",
    "https://www.facebook.com/share/p/14qaVryT22q/",
    "https://www.facebook.com/share/p/1Cyjtorw1p/",
    "https://www.facebook.com/share/p/18MPPJGPJt/",
    "https://www.facebook.com/groups/1016323863626521/permalink/1504235478168688/"
]

cfg = ScoutConfig.from_env()
session = FacebookSession(cfg)
ctx = session.start()
page = ctx.new_page()

resolved_items = []

print(f"Resolving and inspecting all {len(urls)} reference links...")
for i, u in enumerate(urls):
    print(f"\n[{i+1}/{len(urls)}] Navigating: {u}")
    try:
        page.goto(u, timeout=25000)
        time.sleep(3)
        final_url = page.url
        title = page.title()
        body = page.locator('body').inner_text()[:600].replace('\n', ' ')
        
        is_live = ("isn't available" not in body and "غير متوفر" not in body and "Log in" not in title)
        
        # Extract images
        imgs = page.evaluate("""() => {
            const arr = [];
            document.querySelectorAll("img").forEach(im => {
                const s = im.src || "";
                if (s && (s.includes("scontent") || s.includes("fbcdn")) && !s.includes("emoji.php") && !s.includes("rsrc.php")) {
                    arr.push(s);
                }
            });
            return arr;
        }""")
        
        # Extract links (affiliate links)
        links = page.evaluate("""() => {
            return Array.from(document.querySelectorAll("a[href]")).map(a => a.href);
        }""")
        
        aff_links = [l for l in links if any(k in l.lower() for k in ['walmrt.us', 'walmart.com', 'amzn.to', 'a.co', 'amazon.com', 'fashlyst', 'mavely'])]
        
        res = {
            "input_url": u,
            "final_url": final_url.split('?')[0] if '?' in final_url and ('__cft__' in final_url or '__tn__' in final_url) else final_url,
            "title": title,
            "is_live": is_live,
            "body_snippet": body[:250],
            "images_count": len(imgs),
            "sample_img": imgs[0] if imgs else "",
            "affiliate_links": aff_links
        }
        resolved_items.append(res)
        print(f"  -> Final URL: {res['final_url']}")
        print(f"  -> Status: {'LIVE' if is_live else 'DEAD'}")
        print(f"  -> Title: {title[:40]}")
        print(f"  -> Affiliates found: {aff_links}")
    except Exception as e:
        print(f"  -> ERROR: {e}")
        resolved_items.append({
            "input_url": u,
            "is_live": False,
            "error": str(e)
        })

session.browser.close()

with open("data/reports/reference_links_resolved.json", "w", encoding="utf-8") as f:
    json.dump(resolved_items, f, ensure_ascii=False, indent=2)

print("\nDone resolving all reference links! Saved to data/reports/reference_links_resolved.json")
