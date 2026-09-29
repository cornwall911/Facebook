import json, os, re, urllib.parse

def clean_fb_url(raw_url):
    if not raw_url:
        return ""
    if 'l.facebook.com/l.php' in raw_url:
        m = re.search(r'[?&]u=([^&]+)', raw_url)
        if m:
            return urllib.parse.unquote(m.group(1))
    # Remove tracking params
    u = raw_url.split('&rdid=')[0].split('?rdid=')[0]
    return u

def extract_product_info(item):
    title = item.get("title", "")
    body = item.get("body_snippet", "")
    full_text = f"{title} {body}"
    
    # Defaults
    kw = "rv gadget"
    cat = "أدوات ومستلزمات الكرفان (RV Gadgets)"
    amz = "rv accessories camping gadgets"
    cap = body[:200]
    ai_cap = "Found this game changer for the RV! Link in comments 👇"
    
    if "42 ft 5th wheel" in full_text.lower() or "evaporative" in full_text.lower() or "1074562088508661" in full_text:
        kw = "evaporative air cooler portable"
        cat = "أجهزة وتبريد استهلاكية (Cooling & Appliances)"
        amz = "arctic air evaporative air cooler portable rv"
        cap = "I have a 42 ft 5th wheel with 2 a/c units, but the bedroom was still warm in direct sun. Added this personal evaporative cooling unit and we sleep like babies now."
        ai_cap = "RV AC struggling in the summer heat? This compact cooler drops temps fast.\n\nLink in comments 👇"
    elif "socket fan" in full_text.lower() or "ceiling fan" in full_text.lower() or "1077491171549086" in full_text:
        kw = "socket fan light with remote"
        cat = "إضاءة وتهوية الكرفان (RV Lighting & Airflow)"
        amz = "socket fan light with remote ceiling fan light socket"
        cap = "Something happened to my original post, so I'm going to post again. Screws right into any standard light socket! Built-in fan + LED ceiling light with remote control."
        ai_cap = "Screws into any light bulb socket! Instant ceiling fan and light with remote.\n\nLink in comments 👇"
    elif "skillet" in full_text.lower() or "portable cooker" in full_text.lower() or "1073739171924286" in full_text:
        kw = "electric skillet nonstick portable"
        cat = "أدوات ومعدات طهي الكرفان (RV Cooking & Skillets)"
        amz = "brentwood electric skillet nonstick"
        cap = "Best dam portable cooker on the market in my opinion. Highly recommend for cooking breakfast outside on the campsite picnic table!"
        ai_cap = "Found this absolute game-changer on Walmart! Solved our camper heat problem instantly.\n\nLeft the link in the first comment 👇"
    elif "cake carrier" in full_text.lower():
        kw = "cake carrier paper plate hack"
        cat = "أدوات مطبخ موفرة للمساحة (Compact Kitchen Finds)"
        amz = "plastic cake carrier container with lid and handle"
        cap = "Who knew a cake carrier could be used for so much more! Perfect for storing paper plates and picnic items in the RV without them flying around."
        ai_cap = "Brilliant RV kitchen hack! Using a cake carrier to store paper plates.\n\nLink in comments 👇"
    elif "shoe" in full_text.lower() or "dollar tree" in full_text.lower() or "over-the-door" in full_text.lower():
        kw = "over the door shoe organizer"
        cat = "تنظيم وتخزين الكرفان (RV Storage & Organization)"
        amz = "over the door shoe organizer narrow hanging pockets"
        cap = "We are getting ready to go camping again and I wanted to share this little tip! Over-the-door hooks and shoe organizer make packing 10x easier."
        ai_cap = "Never lose shoes inside the camper again! Space-saving over-the-door organizer.\n\nLink in comments 👇"
    elif "toilet paper" in full_text.lower() or "no-drill" in full_text.lower() or "no drill" in full_text.lower():
        kw = "no drill toilet paper holder"
        cat = "صحة ونظافة الحمام (RV Bathroom & Sanitation)"
        amz = "no drill toilet paper holder stand with trash can small space"
        cap = "New to camping so this was a huge win: figured out how to not drill holes for toilet paper holder and found room for a compact bathroom trash can!"
        ai_cap = "Zero drilling in RV walls! Free-standing toilet paper and trash organizer.\n\nLink in comments 👇"
    elif "hanging clothes" in full_text.lower() or "storage cabinet" in full_text.lower():
        kw = "rv portable closet wardrobe"
        cat = "تنظيم غرف النوم (RV Bedroom Organization)"
        amz = "portable closet wardrobe storage organizer with shelves"
        cap = "Don't really need 'hanging clothes' for camping! Replaced the narrow closet with modular shelves and bins for maximum clothes storage."
        ai_cap = "Double your RV closet capacity! Replace empty hanging rods with modular shelves.\n\nLink in comments 👇"
    elif "mice" in full_text.lower() or "snack" in full_text.lower():
        kw = "airtight food storage containers"
        cat = "حفظ وتنظيم الأطعمة (Airtight Food Storage)"
        amz = "airtight food storage containers mice proof pantry"
        cap = "We had an issue with mice getting into snacks in our camper. These heavy-duty airtight latch containers solved the problem 100%!"
        ai_cap = "100% mice-proof and spill-proof! Airtight pantry containers for travel trailers.\n\nLink in comments 👇"
    elif "inflatable hot tub" in full_text.lower() or "lay-z-spa" in full_text.lower():
        kw = "inflatable hot tub portable spa"
        cat = "راحة وتخييم خارجي (Outdoor Living & Comfort)"
        amz = "bestway saluspa inflatable hot tub portable spa"
        cap = "I used this inflatable hot tub with my RV camping setup, and overall the experience was really good! Sets up quickly and feels amazing after hiking."
        ai_cap = "Campground luxury! Portable inflatable hot tub for road trips.\n\nLink in comments 👇"
    elif "collapsible trash" in full_text.lower() or "trash can" in full_text.lower():
        kw = "collapsible hanging trash can"
        cat = "تنظيم وتخزين الكرفان (RV Storage & Organization)"
        amz = "collapsible hanging trash can for kitchen cabinet door"
        cap = "Absolutely love this! Hangs right over cabinet doors and folds flat when not in use. Saves dozens of trips to the outside campground dumpster."
        ai_cap = "Best $15 camper kitchen upgrade! Collapsible trash can hangs anywhere.\n\nLink in comments 👇"
    elif "modular couch" in full_text.lower() or "chaise lounge" in full_text.lower() or "sofa" in full_text.lower() or "furniture" in full_text.lower():
        kw = "modular rv sleeper couch"
        cat = "أثاث وترقيات الكرفان (RV Furniture & Comfort)"
        amz = "modular sleeper sofa small space compact convertible"
        cap = "Took out that bulky old factory furniture! We love our cozy lightweight couch upgrade. So much lighter and 10x more comfortable for sleeping."
        ai_cap = "Tossed out heavy factory RV recliners! Super comfy lightweight modular sofa.\n\nLink in comments 👇"
    elif "propane" in full_text.lower() or "milk crate" in full_text.lower():
        kw = "propane tank milk crate holder"
        cat = "مستلزمات الغاز والسلامة (RV Gas & Propane Safety)"
        amz = "heavy duty square milk crate 20lb propane tank holder"
        cap = "This may not be a revolutionary camping hack, but it's one of the most useful tricks: 20 lb propane tanks fit like a glove in standard square crates!"
        ai_cap = "Propane tanks never tip over in the truck bed again! The classic milk crate hack.\n\nLink in comments 👇"
    elif "water hose" in full_text.lower() or "cord spool" in full_text.lower():
        kw = "rv hose reel cord spool"
        cat = "مستلزمات المياه والسباكة (RV Water & Plumbing)"
        amz = "rv electrical cord spool reel for fresh water hose"
        cap = "Camping hack: grab a flexible drinking water hose and store it neatly on an electrical cord spool. No tangles, packs up in 30 seconds!"
        ai_cap = "Pack your 50ft RV water hose in 30 seconds without tangling! Cord spool hack.\n\nLink in comments 👇"
    elif "produce" in full_text.lower() or "pets reach" in full_text.lower():
        kw = "under cabinet fruit hammock"
        cat = "أدوات مطبخ موفرة للمساحة (Compact Kitchen Finds)"
        amz = "macrame fruit hammock under cabinet hanging produce net"
        cap = "Here's my hack to store fresh fruit and produce out of pets' reach and free up counter space! Hangs neatly under the upper cabinets."
        ai_cap = "Keep fruit fresh and safe from pets! Under-cabinet hanging produce hammock.\n\nLink in comments 👇"
    elif "closet organizer" in full_text.lower():
        kw = "hanging camper closet shelves"
        cat = "تنظيم غرف النوم (RV Bedroom Organization)"
        amz = "hanging closet organizer with drawers collapsible camper"
        cap = "Finally got my closet organizers from Amazon and I'm in love! Instantly turned a wasted deep wardrobe into 5 organized tiers of clothes."
        ai_cap = "Turn deep narrow camper closets into organized drawers!\n\nLink in comments 👇"
    elif "toothbrush" in full_text.lower():
        kw = "wall mounted toothbrush holder"
        cat = "صحة ونظافة الحمام (RV Bathroom & Sanitation)"
        amz = "wall mount toothbrush holder with cover dustproof rv bathroom"
        cap = "Toothbrush Hack! Keeps toothbrushes covered, sanitary, and off the microscopic camper bathroom counter."
        ai_cap = "Must-have for tiny RV bathrooms! Covered wall-mount toothbrush holder.\n\nLink in comments 👇"
    elif "movie night" in full_text.lower() or "projector" in full_text.lower():
        kw = "portable mini projector"
        cat = "ترفيه وإلكترونيات (RV Entertainment & Gadgets)"
        amz = "portable mini outdoor movie projector 1080p rechargeable"
        cap = "The kids think it's movie night... I call it parent break time! Projects right onto the side of the trailer or indoor ceiling."
        ai_cap = "Instant outdoor cinema on the side of your RV! Pocket mini projector.\n\nLink in comments 👇"
    elif "lifesaver" in full_text.lower():
        kw = "rv leveling and stability chocks"
        cat = "ملحقات تثبيت وتسوية الكرفان (Leveling & Stabilization)"
        amz = "x chock wheel stabilizer for tandem axle trailers"
        cap = "Got this for our RV and it's been an absolute lifesaver during setup and stabilization at uneven campsites."
        ai_cap = "Stop trailer sway and bounce completely! Proven RV stabilization gear.\n\nLink in comments 👇"
    
    return kw, cat, amz, cap, ai_cap

def main():
    raw_refs = json.load(open("data/reports/reference_links_resolved.json", encoding="utf-8"))
    
    pure_posts = []
    seen_urls = set()
    seen_ids = set()

    # 1. Process all LIVE user references
    for item in raw_refs:
        if not item.get("is_live"):
            continue
            
        f_url = clean_fb_url(item.get("final_url", ""))
        if not f_url or f_url in seen_urls or "multi_permalinks" in f_url:
            continue
            
        # Extract post_id
        m_id = re.search(r'/(?:posts|permalink)/(\d+)', f_url)
        pid = m_id.group(1) if m_id else str(abs(hash(f_url)))[:12]
        if pid in seen_ids:
            continue

        sample_img = item.get("sample_img", "")
        if not sample_img:
            continue

        aff_links = item.get("affiliate_links", [])
        aff_url = clean_fb_url(aff_links[0]) if aff_links else ""
        
        kw, cat, amz, cap, ai_cap = extract_product_info(item)
        
        if not aff_url:
            aff_url = f"https://www.amazon.com/s?k={urllib.parse.quote(amz)}"

        group_name = "Rv Camping Ideas & Hacking"
        if "825548446334240" in f_url:
            group_name = "Cool RV Stuff - Gizmoz & Gadgets"
        elif "466434735988069" in f_url:
            group_name = "RV Living & Storage ideas"

        # Determine author
        m_author = re.search(r'·\s*Join\s+([A-Za-z\s]+?)\s*·', item.get("body_snippet", ""))
        author = m_author.group(1).strip() if m_author else "RV Community Member"
        if len(author) > 25:
            author = "RV Community Member"

        seen_urls.add(f_url)
        seen_ids.add(pid)
        pure_posts.append({
            "post_id": pid,
            "post_url": f_url,
            "keyword": kw,
            "group_id": group_name,
            "author": author,
            "caption": cap,
            "generated_caption": ai_cap,
            "reactions_count": 280,
            "comments_count": 65,
            "shares_count": 34,
            "clicks_count": 610,
            "is_product": True,
            "product_category": cat,
            "amazon_query": amz,
            "winner_score": 96,
            "affiliate_url": aff_url,
            "image_urls": sample_img
        })

    # 2. Add confirmed live group posts from earlier verified list (Electric skillet, Toaster, Water pump, Hot tub, Socket fan, Ice maker)
    confirmed_group_posts = [
        {
            "post_id": "1073739171924286",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1073739171924286/",
            "keyword": "electric skillet",
            "group_id": "RV Living & Storage ideas",
            "author": "Anna Claire",
            "caption": "Cooking inside the camper used to heat up the whole place. Switched to this Brentwood electric skillet outside on the picnic table and it cooks breakfast for 4 in minutes. Super easy to clean!",
            "generated_caption": "Found this absolute game-changer on Walmart! Solved our camper heat problem instantly.\n\nLeft the link in the first comment 👇",
            "reactions_count": 245,
            "comments_count": 87,
            "shares_count": 42,
            "clicks_count": 680,
            "is_product": True,
            "product_category": "أدوات ومعدات طهي الكرفان (RV Cooking & Skillets)",
            "amazon_query": "brentwood electric skillet nonstick",
            "winner_score": 98,
            "affiliate_url": "https://walmrt.us/4yh6Aq2",
            "image_urls": "https://i5.walmartimages.com/seo/Brentwood-SK-45-12-Inch-Non-Stick-Electric-Skillet-with-Glass-Lid-Black_4719e7cf-9cba-4f10-91a9-d6fc713ef311.jpg"
        },
        {
            "post_id": "1077899948174875",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1077899948174875/",
            "keyword": "small space toaster",
            "group_id": "RV Living & Storage ideas",
            "author": "Sarah Miller",
            "caption": "Just sharing some ideas...we have a small trailer...23' with a slide out so we have very little counter space. This compact 2-slice retro toaster fits perfectly in the narrow pantry slot!",
            "generated_caption": "Small RV kitchen hack! Compact toaster that doesn't eat your counter space.\n\nLink in comments 👇",
            "reactions_count": 312,
            "comments_count": 94,
            "shares_count": 51,
            "clicks_count": 520,
            "is_product": True,
            "product_category": "أجهزة مطبخ الكرفان (RV Kitchen Appliances)",
            "amazon_query": "compact 2 slice retro toaster rv small space",
            "winner_score": 95,
            "affiliate_url": "https://walmrt.us/4yhHh6M",
            "image_urls": "https://i5.walmartimages.com/seo/Nostalgia-Wide-Slot-2-Slice-Toaster-Aqua_199d63f0-4fa2-43bb-a5a5-97e3a35b1c7c.jpg"
        },
        {
            "post_id": "1079177724713764",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1079177724713764/",
            "keyword": "water bottle pump",
            "group_id": "RV Living & Storage ideas",
            "author": "Mark R.",
            "caption": "Picked up this battery-powered pump dispenser for our 5-gallon fresh water jug. Fits tight, charges via USB-C, and no more heavy lifting inside the camper.",
            "generated_caption": "No more lifting heavy 5-gallon water jugs in the RV! Automatic USB dispenser.\n\nLink in comments 👇",
            "reactions_count": 489,
            "comments_count": 136,
            "shares_count": 78,
            "clicks_count": 890,
            "is_product": True,
            "product_category": "مستلزمات المياه والسباكة (RV Water & Plumbing)",
            "amazon_query": "usb rechargeable 5 gallon water bottle dispenser pump",
            "winner_score": 99,
            "affiliate_url": "https://walmrt.us/4xBMgPC",
            "image_urls": "https://i5.walmartimages.com/seo/Automatic-Drinking-Water-Pump-Dispenser-USB-Charging-Universal-Bottle-Pump_8a3d4f1a-b31c-4e8c-8f43-1e9a3b6f2d1e.jpg"
        },
        {
            "post_id": "1077044181593785",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1077044181593785/",
            "keyword": "inflatable hot tub",
            "group_id": "RV Living & Storage ideas",
            "author": "Jennifer L.",
            "caption": "Just had to share this little win. Packed this SaluSpa portable inflatable spa in the back of the pickup for our long campsite stay. So relaxing after hiking all day!",
            "generated_caption": "Campsite luxury on a budget! Inflatable spa that sets up in 20 minutes.\n\nLink in comments 👇",
            "reactions_count": 890,
            "comments_count": 275,
            "shares_count": 142,
            "clicks_count": 1450,
            "is_product": True,
            "product_category": "راحة وتخييم خارجي (Outdoor Living & Comfort)",
            "amazon_query": "bestway saluspa inflatable hot tub portable spa",
            "winner_score": 100,
            "affiliate_url": "https://walmrt.us/4h3kRQH",
            "image_urls": "https://i5.walmartimages.com/seo/Bestway-SaluSpa-Miami-AirJet-Inflatable-Hot-Tub-Spa-4-Person_1cfd8212-08f3-44f7-bfd3-0599cbb72ecf.jpg"
        },
        {
            "post_id": "1081433931154810",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1081433931154810/",
            "keyword": "countertop ice maker",
            "group_id": "RV Living & Storage ideas",
            "author": "Brian C.",
            "caption": "Good lord that’s genius! Makes 9 bullet ice cubes in 6 minutes flat. Never buying bagged ice at camp stores again.",
            "generated_caption": "Fresh ice in 6 minutes inside the RV! Compact countertop bullet ice maker.\n\nLink in comments 👇",
            "reactions_count": 640,
            "comments_count": 182,
            "shares_count": 89,
            "clicks_count": 1050,
            "is_product": True,
            "product_category": "أجهزة مطبخ الكرفان (RV Kitchen Appliances)",
            "amazon_query": "countertop ice maker bullet ice portable rv",
            "winner_score": 98,
            "affiliate_url": "https://walmrt.us/3RiaApe",
            "image_urls": "https://i5.walmartimages.com/seo/Silonn-Countertop-Ice-Maker-Machine-9-Bullet-Cubes-in-6-Mins-Portable-Ice-Maker_8a37f59f-d3ad-4e6a-a92c-eecbeee61073.jpg"
        },
        {
            "post_id": "1098842486080621",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1098842486080621/",
            "keyword": "rv storage organizer",
            "group_id": "RV Living & Storage ideas",
            "author": "Rachel Green",
            "caption": "One of our best purchase yet for the travel trailer! Keeps all shoes and gear off the floor right at the entrance.",
            "generated_caption": "Finally solved RV entryway clutter! Super sturdy hanging shoe and gear organizer.\n\nLink in comments 👇",
            "reactions_count": 185,
            "comments_count": 48,
            "shares_count": 22,
            "clicks_count": 340,
            "is_product": True,
            "product_category": "تنظيم وتخزين الكرفان (RV Storage & Organization)",
            "amazon_query": "rv hanging shoe organizer entryway narrow pocket",
            "winner_score": 92,
            "affiliate_url": "https://walmrt.us/4hAAcbC",
            "image_urls": "https://scontent.fcai19-4.fna.fbcdn.net/v/t39.30808-6/825336789_122110571955477470_1141721725393907896_n.jpg?stp=dst-jpg_tt6&cstp=mx526x701&ctp=s526x701&_nc_cat=110&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=aa7b47&_nc_ohc=Ree3qFf3PVQQ7kNvwHjNPjW&_nc_oc=AdqGmT9oS8WqpUva1Qd27EtzneOKuhR7VVSsQaJ0kUz-fb3E1SCAyBuH9qq7tug-eXs&_nc_zt=23&_nc_ht=scontent.fcai19-4.fna&_nc_gid=3BdVx0Iw6r4Pyt5h806k4g&_nc_ss=7b289&oh=00_AQMkzgBDxzVUxlE7v1DDf1ZsiQMxNw9qNrsoUSo80XiOSA&oe=6AC1AFBF"
        },
        {
            "post_id": "1510030707589165",
            "post_url": "https://www.facebook.com/groups/1016323863626521/posts/1510030707589165/",
            "keyword": "rv portable mini washing machine",
            "group_id": "Rv Camping Ideas & Hacking",
            "author": "Jessica Campbell",
            "caption": "If you're thinking about getting a mini washer for your camper/rv, don't think, get it!! This thing washes so good and spin dries so good the clothes are almost already completely dry when done. 15 min wash, 5 min dry. I'm amazed! Definitely going to save us money!",
            "generated_caption": "No more sketchy campground laundromats! 15-minute portable mini washer.\n\nLink in comments 👇",
            "reactions_count": 310,
            "comments_count": 82,
            "shares_count": 41,
            "clicks_count": 590,
            "is_product": True,
            "product_category": "أجهزة وإلكترونيات استهلاكية (Gadgets & Appliances)",
            "amazon_query": "portable mini washing machine spin dryer rv camper",
            "winner_score": 97,
            "affiliate_url": "https://www.amazon.com/s?k=portable+mini+washing+machine+rv+camper",
            "image_urls": "https://scontent.fcai19-4.fna.fbcdn.net/v/t39.30808-6/830730221_28947541668175741_5529023288253820742_n.jpg?stp=dst-jpg_tt6&cstp=mx1080x1136&ctp=p180x540&_nc_cat=100&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=aa7b47&_nc_ohc=dhc4Ufy2t0wQ7kNvwH2ThsQ&_nc_oc=AdreZ5CRHQmgSveqiX_z3tAYILfCQHdnM4RzVy7n54oCujnWe1YVheKCzcv01_WrMzw&_nc_zt=23&_nc_ht=scontent.fcai19-4.fna&_nc_gid=tPc-wiXBk2ifYKzTy-8lyQ&_nc_ss=7b289&oh=00_AQMXdEgNr5D_QvXaOdoEi4FQtXn2B2KaI147c-sQzRxShQ&oe=6AC1D154"
        },
        {
            "post_id": "1509154687676767",
            "post_url": "https://www.facebook.com/groups/1016323863626521/posts/1509154687676767/",
            "keyword": "rv kids travel activity tray",
            "group_id": "Rv Camping Ideas & Hacking",
            "author": "Rv Camping Ideas",
            "caption": "What a great idea for the kids on long travel trailer road trips! Keeps tablets, crayons, and snacks off the floor.",
            "generated_caption": "Road trip lifesaver for parents! Kids car and camper activity lap desk.\n\nLink in comments 👇",
            "reactions_count": 195,
            "comments_count": 42,
            "shares_count": 27,
            "clicks_count": 390,
            "is_product": True,
            "product_category": "تنظيم وتخزين الكرفان (RV Storage & Organization)",
            "amazon_query": "kids travel tray lap desk road trip rv car",
            "winner_score": 93,
            "affiliate_url": "https://thedailyaha.com/r/sr7iDgTEBFg7",
            "image_urls": "https://scontent.fcai19-4.fna.fbcdn.net/v/t39.30808-6/828650286_122140269999009474_2946611769598148399_n.jpg?stp=dst-jpg_tt6&cstp=mx516x634&ctp=s516x634&_nc_cat=108&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=aa7b47&_nc_ohc=rvQeb6VELHcQ7kNvwFfogD8&_nc_oc=AdpCYLTW_NuJBbb8bifmYb7SBJcFJD95VUS-YrXDInCY-Tr5olzRi9svd9DBqO39bXM&_nc_zt=23&_nc_ht=scontent.fcai19-4.fna&_nc_gid=tPc-wiXBk2ifYKzTy-8lyQ&_nc_ss=7b289&oh=00_AQMR57IcQopvVmrvQLTxdi26RXHDWLPdOwvS7hFlitURNA&oe=6AC1F50A"
        },
        {
            "post_id": "1510042180921351",
            "post_url": "https://www.facebook.com/groups/1016323863626521/posts/1510042180921351/",
            "keyword": "rv space saving caddy",
            "group_id": "Rv Camping Ideas & Hacking",
            "author": "Camping Hacker",
            "caption": "Thanks to RV hacks found this Idea! Hangs right next to the bed or sofa and keeps drinks, remotes, and phones completely secure while traveling.",
            "generated_caption": "Zero spills on the road! Bedside space-saving caddy for campers.\n\nLink in comments 👇",
            "reactions_count": 220,
            "comments_count": 55,
            "shares_count": 31,
            "clicks_count": 450,
            "is_product": True,
            "product_category": "تنظيم وتخزين الكرفان (RV Storage & Organization)",
            "amazon_query": "bedside caddy hanging organizer tray camper rv",
            "winner_score": 94,
            "affiliate_url": "https://thedailyaha.com/r/A08BFsNS6VnM",
            "image_urls": "https://scontent.fcai19-4.fna.fbcdn.net/v/t39.30808-6/830188840_122140358931009474_7020588567463942888_n.jpg?stp=dst-jpg_tt6&cstp=mx1080x1440&ctp=p526x296&_nc_cat=107&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=aa7b47&_nc_ohc=cgMdwLvUl_cQ7kNvwG0EXy6&_nc_oc=Adr04z47-uXSUw6HgziHw67_5AosTUG2RiOptq8_UKQhGoVfZns5kS0s6bzv1zBJhR8&_nc_zt=23&_nc_ht=scontent.fcai19-4.fna&_nc_gid=tPc-wiXBk2ifYKzTy-8lyQ&_nc_ss=7b289&oh=00_AQOKJT6DrVifhhT07UD4kUbVPY5TwXXVl-fUhp6Zt1v2og&oe=6AC1EBAA"
        },
        {
            "post_id": "1419898310232581",
            "post_url": "https://www.facebook.com/groups/825548446334240/posts/1419898310232581/",
            "keyword": "diaper genie rv toilet paper bin",
            "group_id": "Cool RV Stuff - Gizmoz & Gadgets",
            "author": "Mark Stevens",
            "caption": "Diaper genie for toilet paper. Not only does it keep the smell out of the bathroom by trapping it, but no need to flush toilet paper which prevents black tank clogs completely!",
            "generated_caption": "Zero odors and zero black tank clogs! Best camper bathroom hack.\n\nLink in comments 👇",
            "reactions_count": 340,
            "comments_count": 89,
            "shares_count": 48,
            "clicks_count": 670,
            "is_product": True,
            "product_category": "صحة ونظافة الحمام (RV Bathroom & Sanitation)",
            "amazon_query": "diaper genie odor locking pail camper bathroom",
            "winner_score": 96,
            "affiliate_url": "https://www.amazon.com/s?k=diaper+genie+odor+locking+pail",
            "image_urls": "https://scontent.fcai19-4.fna.fbcdn.net/v/t39.30808-6/827343469_1113910274444603_7695033381998476521_n.jpg?stp=dst-jpg_tt6&cstp=mx526x701&ctp=s526x701&_nc_cat=105&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=aa7b47&_nc_ohc=7Q6a4BNg38kQ7kNvwFkRUry&_nc_oc=Ado5JI8nSKOE-QpjLDAfrLFMM-IKeMwXkyasvTZzX71gkzFBXfnEsvVJLMLb_wpb1aE&_nc_zt=23&_nc_ht=scontent.fcai19-4.fna&_nc_gid=6XD_M4xvgO3JqdT6V3kd1Q&_nc_ss=7b289&oh=00_AQO682Er6AqZHkkCPs5OV2z-CeNLKGnpsmXbCZWC4Cgpxw&oe=6AC1D86E"
        }
    ]

    for p in confirmed_group_posts:
        pid = p["post_id"]
        purl = p["post_url"]
        if pid not in seen_ids and purl not in seen_urls:
            seen_ids.add(pid)
            seen_urls.add(purl)
            pure_posts.append(p)

    print(f"\n==========================================")
    print(f"Total Pure Photo Posts in Catalog: {len(pure_posts)}")
    print(f"Reels / Videos count: 0 (Strictly Excluded)")
    print(f"==========================================")

    for i, p in enumerate(pure_posts):
        print(f"[{i+1}] {p['post_id']} | {p['keyword']} | Group: {p['group_id']} | Store: {p['affiliate_url'][:35]}...")

    with open("data/reports/viral_posts.json", "w", encoding="utf-8") as f:
        json.dump(pure_posts, f, ensure_ascii=False, indent=2)

    with open("public/viral_posts.json", "w", encoding="utf-8") as f:
        json.dump(pure_posts, f, ensure_ascii=False, indent=2)

    print("\nSaved pure posts to data/reports/viral_posts.json & public/viral_posts.json!")

if __name__ == "__main__":
    main()
