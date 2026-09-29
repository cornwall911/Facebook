from fb_winner_scout.config import ScoutConfig
from fb_winner_scout.session import FacebookSession
from fb_winner_scout.parser import extract_affiliate_link
import time, json, re, urllib.parse

def clean_link(raw_link):
    if not raw_link:
        return ""
    if 'l.facebook.com/l.php' in raw_link:
        m = re.search(r'[?&]u=([^&]+)', raw_link)
        if m:
            return urllib.parse.unquote(m.group(1))
    return raw_link

def main():
    photos = json.load(open("data/reports/scanned_media_photos.json", encoding="utf-8"))
    print(f"Total raw photos to process: {len(photos)}")

    cfg = ScoutConfig.from_env()
    session = FacebookSession(cfg)
    ctx = session.start()
    page = ctx.new_page()

    resolved_posts = []
    seen_post_urls = set()

    # Process up to 50 items
    for idx, p in enumerate(photos[:50]):
        ph_url = p.get("photo_href") or p.get("post_url")
        gname = p.get("group_name", "RV Community")
        img = p.get("img", "")
        
        print(f"\n[{idx+1}/50] Processing: {gname}")
        try:
            page.goto(ph_url, timeout=18000)
            time.sleep(2.5)
            
            body = page.locator('body').inner_text()[:600].replace('\n', ' ')
            if "isn't available" in body or "غير متوفر" in body:
                print("  -> Post unavailable / deleted, skipping.")
                continue

            # Extract post URL from timestamp anchor
            post_url = page.evaluate("""() => {
                const anchors = Array.from(document.querySelectorAll('a[href]'));
                const postA = anchors.find(a => {
                    const h = a.href;
                    return (h.includes('/posts/') || h.includes('/permalink/')) && !h.includes('comment_id=') && (a.innerText || a.getAttribute('aria-label') || '').match(/\\d+\\s*(?:m|h|d|min|hr|day|Aug|Jul|Jun|Sep|Oct|Nov|Dec)/);
                });
                return postA ? postA.href : null;
            }""")

            if not post_url:
                # Fallback to base photo url
                post_url = p.get("post_url")

            # Clean tracking from post_url
            post_url = post_url.split('?')[0] if '?' in post_url else post_url
            
            if post_url in seen_post_urls:
                print("  -> Duplicate post_url, skipping.")
                continue

            # Extract author
            author = page.evaluate("""() => {
                const h2 = document.querySelector('h2 a, h3 a, strong a, a[role="link"]');
                return h2 ? h2.innerText.trim() : '';
            }""") or "RV Community Member"

            # Extract caption
            caption = page.evaluate("""() => {
                const textNodes = Array.from(document.querySelectorAll("div[dir='auto']"));
                for (const t of textNodes) {
                    const txt = t.innerText.trim();
                    if (txt.length > 20 && !txt.includes("Log in") && !txt.includes("Like") && !txt.includes("Comment")) {
                        return txt;
                    }
                }
                return '';
            }""")

            # Extract affiliate links
            aff_link = page.evaluate("""() => {
                const links = Array.from(document.querySelectorAll('a[href]')).map(a => a.href);
                const found = links.find(h => h.includes('fashlyst') || h.includes('walmrt') || h.includes('amazon') || h.includes('thedailyaha') || h.includes('amzn.to') || h.includes('a.co'));
                return found || '';
            }""")

            clean_aff = clean_link(aff_link)
            
            # Extract high-res image
            hi_img = page.evaluate("""() => {
                const mainIm = document.querySelector("img[data-visualcompletion='media-vc-image'], img[style*='cursor']");
                return mainIm ? mainIm.src : '';
            }""") or img

            seen_post_urls.add(post_url)
            pid = post_url.rstrip('/').split('/')[-1]
            
            resolved_posts.append({
                "post_id": pid,
                "post_url": post_url,
                "group_name": gname,
                "author": author,
                "caption": caption or f"Essential RV gear recommendation from {author} in {gname}.",
                "affiliate_url": clean_aff,
                "image_url": hi_img
            })
            print(f"  -> Extracted! Post: {post_url} | Author: {author} | Aff: {clean_aff[:30] if clean_aff else 'None'}")
        except Exception as e:
            print(f"  -> Error: {e}")

    session.browser.close()

    print(f"\n==========================================")
    print(f"Total Successfully Resolved: {len(resolved_posts)}")
    print(f"==========================================")

    with open("data/reports/resolved_media_posts.json", "w", encoding="utf-8") as f:
        json.dump(resolved_posts, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
