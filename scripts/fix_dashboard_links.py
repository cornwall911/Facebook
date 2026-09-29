import json
import re

def fix_links():
    with open("data/reports/viral_posts.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    real_fb_posts = []
    other_products = []

    for p in posts:
        post_url = p.get("post_url", "")
        if "facebook.com" in post_url and ("/posts/" in post_url or "multi_permalinks=" in post_url or "/permalink/" in post_url):
            # Clean and ensure validity
            p["has_direct_fb_post"] = True
            real_fb_posts.append(p)
        else:
            # Synthetic / user provided link without direct FB post URL
            aff_url = p.get("affiliate_url", "")
            kw = p.get("keyword", "")
            cap = p.get("caption", "")

            # Determine product search query for Facebook
            # Extract slug or code from affiliate URL
            query = ""
            if "fashlyst.com/r/" in aff_url:
                code = aff_url.split("/r/")[-1].split("?")[0].strip()
                query = code
                group_id = "466434735988069"
            elif "walmrt.us/" in aff_url:
                code = aff_url.split("walmrt.us/")[-1].split("?")[0].strip()
                query = code
                group_id = "466434735988069"
            elif "walmart.com/ip/" in aff_url:
                slug = aff_url.split("/ip/")[1].split("/")[0].replace("-", " ")
                query = " ".join(slug.split()[:4])
                group_id = "466434735988069"
            elif "amazon.com" in aff_url:
                query = kw or "rv gadget"
                group_id = "RVhackcamp"
            else:
                query = kw or "product"
                group_id = "466434735988069"

            # Create Facebook group search URL so it NEVER opens the store link!
            fb_search_url = f"https://www.facebook.com/groups/{group_id}/search/?q={urllib.parse.quote(query)}"
            p["post_url"] = fb_search_url
            p["has_direct_fb_post"] = False
            other_products.append(p)

    # Sort real FB posts by reactions descending
    real_fb_posts.sort(key=lambda x: (x.get("clicks_count", 0), x.get("reactions_count", 0)), reverse=True)

    # Final combined list: REAL FACEBOOK POSTS FIRST!
    combined = real_fb_posts + other_products

    with open("data/reports/viral_posts.json", "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    with open("public/viral_posts.json", "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"Total posts: {len(combined)}")
    print(f"Direct Facebook Posts (Ranked #1-#25): {len(real_fb_posts)}")
    print(f"Facebook Group Search Posts (Ranked #26+): {len(other_products)}")
    print("Zero posts now have store links in post_url!")

if __name__ == "__main__":
    import urllib.parse
    fix_links()
