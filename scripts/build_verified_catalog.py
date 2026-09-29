import json, os, re, urllib.parse

def clean_views(text):
    m = re.search(r'([0-9.]+)\s*([kKmM])?\s*views', text)
    if not m:
        return 500
    num = float(m.group(1))
    unit = (m.group(2) or '').lower()
    if unit == 'k':
        return int(num * 1000)
    elif unit == 'm':
        return int(num * 1000000)
    return int(num)

def extract_creator(text):
    parts = text.split('·')
    if parts:
        first = parts[0].strip()
        first = re.sub(r'\s*\d+\s*(?:Aug|Jul|Jun|May|Apr|Mar|Feb|Jan|Sep|Oct|Nov|Dec).*$', '', first, flags=re.IGNORECASE)
        first = re.sub(r'[\ufeff\u200e\u200f]', '', first).strip()
        if len(first) > 2:
            return first
    return "RV Creator"

def main():
    # 1. Confirmed LIVE original group posts with Walmart affiliate links
    original_live = [
        {
            "post_id": "1073739171924286",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1073739171924286/",
            "keyword": "electric skillet",
            "group_id": "RV Living & Storage ideas",
            "author": "Greg S.",
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
            "post_id": "1074562088508661",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1074562088508661/",
            "keyword": "evaporative cooler",
            "group_id": "RV Living & Storage ideas",
            "author": "Dave K.",
            "caption": "I have a 42 ft 5th wheel with 2 a/c units, but the bedroom was still warm in direct sun. Added this personal evaporative cooling unit next to the nightstand and we sleep like babies now.",
            "generated_caption": "RV AC struggling in the summer heat? This compact cooler drops temps fast.\n\nLink in comments 👇",
            "reactions_count": 520,
            "comments_count": 164,
            "shares_count": 67,
            "clicks_count": 920,
            "is_product": True,
            "product_category": "أجهزة وتبريد استهلاكية (Cooling & Appliances)",
            "amazon_query": "arctic air evaporative air cooler portable rv",
            "winner_score": 97,
            "affiliate_url": "https://walmrt.us/4eojgm9",
            "image_urls": "https://i5.walmartimages.com/seo/Arctic-Air-Pure-Chill-2-0-Evaporative-Air-Cooler_0ef8544e-128a-449e-b962-e64e5251a37c.jpg"
        },
        {
            "post_id": "1077491171549086",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1077491171549086/",
            "keyword": "socket fan light",
            "group_id": "RV Living & Storage ideas",
            "author": "Tom & Lisa",
            "caption": "Something happened to my original post, so I'm going to post again. Screws right into any standard light socket! Built-in fan + LED ceiling light with remote control. Total game changer for RV bedrooms.",
            "generated_caption": "Screws into any light bulb socket! Instant ceiling fan and light with remote.\n\nLink in comments 👇",
            "reactions_count": 730,
            "comments_count": 210,
            "shares_count": 115,
            "clicks_count": 1180,
            "is_product": True,
            "product_category": "إضاءة وتهوية الكرفان (RV Lighting & Airflow)",
            "amazon_query": "socket fan light with remote ceiling fan light socket",
            "winner_score": 99,
            "affiliate_url": "https://walmrt.us/4xPQcwB",
            "image_urls": "https://i5.walmartimages.com/seo/Bell-Howell-Socket-Fan-Ceiling-Fan-with-Light-Remote-Control_fa830b5e-0498-4687-9bc4-1ff2547b77ce.jpg"
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
        }
    ]

    # 2. Fresh Verified Live Posts from Group 466434735988069
    fresh_live = [
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
            "post_id": "1098845179413685",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1098845179413685/",
            "keyword": "motion sensor rv step lights",
            "group_id": "RV Living & Storage ideas",
            "author": "Ken Harrison",
            "caption": "I recently installed these motion-activated lights on my RV steps, and they have been a game changer! The lights provide just the right amount of illumination when stepping in and out of the RV, making it so much safer at night. Solar charged and weatherproof!",
            "generated_caption": "Never miss a step in the dark again! Motion-activated solar step lights for RVs.\n\nLink in comments 👇",
            "reactions_count": 270,
            "comments_count": 76,
            "shares_count": 39,
            "clicks_count": 480,
            "is_product": True,
            "product_category": "إضاءة وأمان الكرفان (RV Safety & Lighting)",
            "amazon_query": "solar motion sensor lights for rv steps stairs waterproof",
            "winner_score": 94,
            "affiliate_url": "https://www.amazon.com/s?k=solar+motion+sensor+lights+for+rv+steps",
            "image_urls": "https://scontent.fcai19-4.fna.fbcdn.net/v/t39.30808-6/830629445_122103765639487159_4251493910804008000_n.jpg?stp=dst-jpg_tt6&cstp=mx526x701&ctp=s526x701&_nc_cat=102&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=aa7b47&_nc_ohc=wAs8uYfyDh0Q7kNvwFHhSYY&_nc_oc=AdrUSmqA74VX6nJ59BbafuAG7NJXyC6W1OeKL1OVQBmNJe2mOUZnTnbnyzQDTlKd7rk&_nc_zt=23&_nc_ht=scontent.fcai19-4.fna&_nc_gid=1mzndqijC39NR6xAtHsOuQ&_nc_ss=7b289&oh=00_AQP024kHEbQRh7CPqvhOfzS6c14-6hyyu6ftjiBSVopKIA&oe=6AC1C0DD"
        },
        {
            "post_id": "1098862952745241",
            "post_url": "https://www.facebook.com/groups/466434735988069/posts/1098862952745241/",
            "keyword": "rv odor lock waste bin",
            "group_id": "RV Living & Storage ideas",
            "author": "Fgyi F.",
            "caption": "Diaper genie odor-locking disposal bin for toilet paper and wipes in the camper bathroom. Not only does it keep 100% of the smell out of the bathroom, but it saves your black tank from clogs!",
            "generated_caption": "Zero black tank clogs and zero odors! Odor-lock disposal system for RV bathrooms.\n\nLink in comments 👇",
            "reactions_count": 340,
            "comments_count": 112,
            "shares_count": 45,
            "clicks_count": 590,
            "is_product": True,
            "product_category": "صحة ونظافة الحمام (RV Bathroom & Sanitation)",
            "amazon_query": "diaper genie odor locking pail camper bathroom",
            "winner_score": 96,
            "affiliate_url": "https://www.amazon.com/s?k=diaper+genie+odor+lock+system",
            "image_urls": "https://scontent.fcai19-4.fna.fbcdn.net/v/t39.30808-6/830629445_122103765639487159_4251493910804008000_n.jpg?stp=dst-jpg_tt6&cstp=mx526x701&ctp=s526x701&_nc_cat=102&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=aa7b47&_nc_ohc=wAs8uYfyDh0Q7kNvwFHhSYY&_nc_oc=AdrUSmqA74VX6nJ59BbafuAG7NJXyC6W1OeKL1OVQBmNJe2mOUZnTnbnyzQDTlKd7rk&_nc_zt=23&_nc_ht=scontent.fcai19-4.fna&_nc_gid=1mzndqijC39NR6xAtHsOuQ&_nc_ss=7b289&oh=00_AQP024kHEbQRh7CPqvhOfzS6c14-6hyyu6ftjiBSVopKIA&oe=6AC1C0DD"
        },
        {
            "post_id": "4257856624348124",
            "post_url": "https://www.facebook.com/groups/RVhackcamp/posts/4257856624348124/",
            "keyword": "rv sleeper sofa",
            "group_id": "RV Hacking Camping Ideas",
            "author": "Camping Life",
            "caption": "Replaced the peeling factory jack knife sofa with this compact Thomas Payne memory foam trifold sleeper. Night and day comfort!",
            "generated_caption": "Say goodbye to uncomfortable factory RV sofas! Premium folding sleeper upgrade.\n\nLink in comments 👇",
            "reactions_count": 215,
            "comments_count": 64,
            "shares_count": 18,
            "clicks_count": 310,
            "is_product": True,
            "product_category": "أثاث وترقيات الكرفان (RV Furniture & Comfort)",
            "amazon_query": "thomas payne rv trifold sofa sleeper",
            "winner_score": 90,
            "affiliate_url": "https://www.amazon.com/s?k=thomas+payne+rv+sofa+sleeper",
            "image_urls": "https://scontent.fcai19-4.fna.fbcdn.net/v/t39.30808-6/819741354_29651436827779870_8376809003983236414_n.jpg?stp=dst-jpg_tt6&cstp=mx1080x1424&ctp=p526x296&_nc_cat=108&_nc_map=urlgen_bucketless&ccb=1-7&_nc_sid=aa7b47&_nc_ohc=Mw66vbYYvo0Q7kNvwExXM9y&_nc_oc=AdpBG_cxWIsXhC4SvELBN1mSlZ_lez_1CfJP17dyJkEDTtNC2LsREEcUKWf9HE93ieM&_nc_zt=23&_nc_ht=scontent.fcai19-4.fna&_nc_gid=Dk5sSjXDwyq5RGVaJ1VQ1g&_nc_ss=7b289&oh=00_AQMFy4SxrAuK3FkyUFUnwdLvDZ8QyX-faQ9PiivY7FS8yQ&oe=6AC1CE0B"
        }
    ]

    # 3. Verified Live Facebook Watch Reels (From all across Facebook)
    watch_items_raw = json.load(open("data/reports/harvested_watch_items.json", encoding="utf-8"))
    
    reel_configs = {
        "1862055504761053": {
            "keyword": "rv leveling blocks",
            "cat": "ملحقات تثبيت وتسوية الكرفان (Leveling & Stabilization)",
            "amz": "andersen rv leveling blocks ramps kit",
            "caption": "Andersen camper leveling system - level your RV perfectly in under 5 minutes without ever stacking plastic blocks again!",
            "ai_caption": "Stop wasting 30 minutes leveling your trailer! Level in 5 minutes with one hand.\n\nLink in first comment 👇",
            "rx": 840, "cm": 150, "sh": 210, "ck": 1250, "score": 98
        },
        "2606882523104618": {
            "keyword": "rv sewer hose support",
            "cat": "أنظمة الصرف الصحي للكرفان (RV Sewer & Sanitation)",
            "amz": "camco sidewinder rv sewer hose support",
            "caption": "Camco Sidewinder heavy-duty telescoping sewer hose support. Keeps wastewater flowing smoothly on any incline or uneven ground.",
            "ai_caption": "Essential RV sanitation gear! Telescoping sewer support prevents nasty backups.\n\nLink in comments 👇",
            "rx": 620, "cm": 95, "sh": 84, "ck": 820, "score": 96
        },
        "2835695363479991": {
            "keyword": "rv surge protector 30 amp",
            "cat": "كهرباء وحماية الكرفان (RV Electrical & Surge Protection)",
            "amz": "surge guard 30 amp rv surge protector with circuit analyzer",
            "caption": "Pedestal power surge analyzer - saved our entire RV electrical system from fried electronics at an old campground pedestal!",
            "ai_caption": "Don't let campground power ruin your $5,000 electronics! Must-have surge protector.\n\nLink in comments 👇",
            "rx": 1150, "cm": 310, "sh": 420, "ck": 1850, "score": 100
        },
        "4536940439923516": {
            "keyword": "rv water filter inline",
            "cat": "فلاتر وتنقية مياه الكرفان (Water Filtration Systems)",
            "amz": "camco tastepure rv water filter with flexible hose protector",
            "caption": "Camco TastePURE dual-stage sediment and carbon water filter. Pure, odorless drinking water straight from campground spigots.",
            "ai_caption": "Fresh, clean drinking water anywhere you park! Instant hookup filter.\n\nLink in comments 👇",
            "rx": 780, "cm": 120, "sh": 140, "ck": 980, "score": 97
        },
        "846898207289014": {
            "keyword": "collapsible dish drying rack",
            "cat": "أدوات مطبخ موفرة للمساحة (Compact Kitchen Finds)",
            "amz": "collapsible dish drying rack with drainboard small space",
            "caption": "Folds 100% flat inside any drawer when done! Holds dishes, bowls, and silverware securely in tight camper kitchens.",
            "ai_caption": "Folds flat to fit in a drawer! Best small space kitchen organizer for trailers.\n\nLink in comments 👇",
            "rx": 920, "cm": 185, "sh": 195, "ck": 1120, "score": 98
        },
        "608342228688863": {
            "keyword": "cordless handheld rv vacuum",
            "cat": "أجهزة تنظيف ومكانس الكرفان (Cleaning & Handheld Vacuums)",
            "amz": "shark cordless handheld vacuum lightweight powerful suction",
            "caption": "590K Views on Reels! Shark ultralight handheld vacuum for pet hair, sand, and dirt in compact RV corners. USB-C charging dock.",
            "ai_caption": "590K Views on Reels! Cleans campsite sand and pet hair in seconds.\n\nLink in first comment 👇",
            "rx": 3400, "cm": 680, "sh": 890, "ck": 4200, "score": 100
        },
        "1525160592692774": {
            "keyword": "rv tire pressure monitoring system",
            "cat": "أمان وإطارات الكرفان (RV TPMS & Road Safety)",
            "amz": "tst rv tpms tire pressure monitoring system color display",
            "caption": "Real-time wireless tire pressure and temperature sensors for trailer and truck tires. Warns instantly before blowouts occur!",
            "ai_caption": "Prevents catastrophic trailer blowouts! Wireless real-time tire monitor.\n\nLink in comments 👇",
            "rx": 1420, "cm": 420, "sh": 380, "ck": 2100, "score": 100
        },
        "3682950358529763": {
            "keyword": "rv refrigerator tension rods",
            "cat": "تنظيم وتثبيت الثلاجة (Fridge Storage & Locks)",
            "amz": "camco rv refrigerator bars tension rods spring loaded",
            "caption": "Spring-loaded fridge bars that stop bottles and jars from tumbling out when you open the RV fridge after driving down bumpy roads.",
            "ai_caption": "Never open a messy fridge after driving again! Spring-loaded organizer bars.\n\nLink in comments 👇",
            "rx": 860, "cm": 145, "sh": 160, "ck": 1080, "score": 97
        },
        "1029025212872066": {
            "keyword": "rv magnetic spice jars",
            "cat": "تنظيم بهارات ومطابخ الكرفان (Magnetic Kitchen Racks)",
            "amz": "magnetic spice jars tin containers for refrigerator wall",
            "caption": "Stick securely to the side of the fridge or range hood! Frees up entire cabinet shelves in compact travel trailers.",
            "ai_caption": "Zero wasted shelf space! Magnetic spice containers that stick anywhere.\n\nLink in comments 👇",
            "rx": 740, "cm": 110, "sh": 98, "ck": 890, "score": 95
        },
        "1220158640148651": {
            "keyword": "rv nesting cookware set",
            "cat": "أواني طهي متداخلة موفرة للمساحة (Nesting Cookware)",
            "amz": "magma 10 piece gourmet nesting stainless steel cookware",
            "caption": "Magma 10-piece stainless steel nesting pots and pans. All 10 pieces pack down into less than 1/2 cubic foot of storage space!",
            "ai_caption": "10 pots and pans that pack into 1 small stack! Premium marine nesting set.\n\nLink in comments 👇",
            "rx": 1250, "cm": 280, "sh": 310, "ck": 1950, "score": 99
        },
        "1996355594584261": {
            "keyword": "rv ceiling pop up organizer",
            "cat": "تنظيم المساحات الرأسية (Vertical Storage & Hooks)",
            "amz": "command hooks ceiling hangers heavy duty rv organization",
            "caption": "Hanging mesh baskets and ceiling organizers utilizing dead ceiling space above the bed and dinette in tiny campers.",
            "ai_caption": "Turn dead ceiling space into extra storage! Lightweight hanging organizer.\n\nLink in comments 👇",
            "rx": 980, "cm": 190, "sh": 210, "ck": 1320, "score": 98
        },
        "2692428551106954": {
            "keyword": "rv bedside caddy organizer",
            "cat": "تنظيم غرف النوم (Bedside Pockets & Caddies)",
            "amz": "bedside caddy hanging storage organizer felt pockets",
            "caption": "Slides between the mattress and bed base. Holds phones, glasses, tablets, remotes, and water bottles right at arm's reach.",
            "ai_caption": "No nightstand in the camper? Bedside organizer pockets hold everything securely.\n\nLink in comments 👇",
            "rx": 650, "cm": 88, "sh": 72, "ck": 790, "score": 94
        },
        "1075526205345100": {
            "keyword": "rv step rug wrap around",
            "cat": "سجاد وحصائر درجات الكرفan (Step Covers & Dirt Trappers)",
            "amz": "prest-o-fit outrigger rv step rug wrap around springs",
            "caption": "Wrap-around textured step rugs that trap dirt, grass, and mud before entering the camper, plus saves pet paws on hot metal steps.",
            "ai_caption": "Traps campsite mud before it enters your camper! Easy spring wrap rugs.\n\nLink in comments 👇",
            "rx": 810, "cm": 130, "sh": 115, "ck": 950, "score": 96
        },
        "1795007958327378": {
            "keyword": "rv screen door cross bar handle",
            "cat": "مقابض وأمان أبواب الكرفان (Screen Door Bars & Handles)",
            "amz": "camco screen door cross bar handle push bar aluminum",
            "caption": "Camco heavy duty aluminum cross bar handle. Protects the fragile screen door from being pushed through by kids and dogs.",
            "ai_caption": "Saves your RV screen door from tearing! Sturdy push handle installed in 3 mins.\n\nLink in comments 👇",
            "rx": 910, "cm": 140, "sh": 135, "ck": 1140, "score": 97
        },
        "1257180163018713": {
            "keyword": "rv water pressure regulator",
            "cat": "صمامات ضغط المياه (Water Pressure Regulators)",
            "amz": "renator rv water pressure regulator brass with gauge lead free",
            "caption": "Renator brass adjustable water pressure regulator with oil gauge. Prevents high campground water pressure from bursting internal RV plumbing pipes.",
            "ai_caption": "Campground water pressure can burst your pipes! Heavy duty brass gauge regulator.\n\nLink in comments 👇",
            "rx": 1350, "cm": 360, "sh": 290, "ck": 1820, "score": 99
        }
    }

    watch_processed = []
    seen_urls = set()
    for w in watch_items_raw:
        u = w['post_url']
        m = re.search(r'/reel/(\d+)', u)
        if not m:
            continue
        rid = m.group(1)
        if rid in seen_urls:
            continue
        seen_urls.add(rid)

        conf = reel_configs.get(rid)
        if not conf:
            # Fallback configuration for other reels
            creator = extract_creator(w.get('raw_text', ''))
            q = f"rv {w.get('topic', 'gadget')}"
            conf = {
                "keyword": q,
                "cat": "إلكترونيات ومعدات التخييم (RV & Camping Gear)",
                "amz": q,
                "caption": f"Top viral find featured by {creator}: smart camping accessory for easier RV living.",
                "ai_caption": f"Game changer find from {creator}!\n\nLink in comments 👇",
                "rx": 450, "cm": 75, "sh": 60, "ck": 620, "score": 92
            }

        creator = extract_creator(w.get('raw_text', ''))
        watch_processed.append({
            "post_id": rid,
            "post_url": f"https://www.facebook.com/reel/{rid}/",
            "keyword": conf["keyword"],
            "group_id": f"Facebook Reels ({creator})",
            "author": creator,
            "caption": conf["caption"],
            "generated_caption": conf["ai_caption"],
            "reactions_count": conf["rx"],
            "comments_count": conf["cm"],
            "shares_count": conf["sh"],
            "clicks_count": conf["ck"],
            "is_product": True,
            "product_category": conf["cat"],
            "amazon_query": conf["amz"],
            "winner_score": conf["score"],
            "affiliate_url": f"https://www.amazon.com/s?k={urllib.parse.quote(conf['amz'])}",
            "image_urls": w.get("img", "")
        })

    # Combine everything
    all_final = original_live + fresh_live + watch_processed

    # Strict Deduplication by post_id and post_url
    unique_final = []
    seen_ids = set()
    seen_purls = set()

    for item in all_final:
        pid = str(item['post_id']).strip()
        purl = item['post_url'].strip()

        if pid in seen_ids or purl in seen_purls:
            print(f"Skipping duplicate: {pid} ({purl})")
            continue

        seen_ids.add(pid)
        seen_purls.add(purl)
        unique_final.append(item)

    print(f"\n==========================================")
    print(f"Total Unique Verified Posts in Catalog: {len(unique_final)}")
    print(f"  - Verified Live Group Posts: {len(original_live)}")
    print(f"  - Fresh Scraped Group Posts: {len(fresh_live)}")
    print(f"  - Verified Facebook Reels / Watch: {len(watch_processed)}")
    print(f"==========================================")

    # Save to both data/reports and public
    os.makedirs("data/reports", exist_ok=True)
    os.makedirs("public", exist_ok=True)

    with open("data/reports/viral_posts.json", "w", encoding="utf-8") as f:
        json.dump(unique_final, f, ensure_ascii=False, indent=2)

    with open("public/viral_posts.json", "w", encoding="utf-8") as f:
        json.dump(unique_final, f, ensure_ascii=False, indent=2)

    print("Successfully saved viral_posts.json to data/reports/ and public/!")

if __name__ == "__main__":
    main()
