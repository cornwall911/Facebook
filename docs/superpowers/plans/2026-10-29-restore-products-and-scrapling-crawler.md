# Restore Products & Scrapling Fierce Crawler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore all previous viral/catalog products (75+ items) to the dashboard, fix frontend filtering so all product cards display immediately, verify updated Facebook cookies, and upgrade crawler to an aggressive, multi-layer scraper using Scrapling Selector and in-group searches.

**Architecture:** 
1. Storage unification: create `load_all_dashboard_posts()` in `storage.py` that merges and deduplicates historical winner posts (`viral_posts.json`), catalog posts (`catalog_posts.json`), and live scraped posts (`source_posts.json`) into normalized post dicts.
2. Dashboard fix: update `dashboard.py` to use unified posts, fix `matchesPhysical` logic to treat any post with `product_url`, `affiliate_url`, or `is_product` as a physical product, and remove default forced checking of `physical-only`.
3. Cookie verification: cookies injected into `cookies.json` and verified with `FacebookSession` (confirmed `logged-in`).
4. Fierce Scrapling Crawler: upgrade `crawler.py` to parse post HTML via Scrapling `Selector` (deep link extraction from DOM & text regex), implement aggressive `scrollIntoView()` feed trigger, and support targeted group keyword searches (`/search/?q=walmart`, `amazon`, etc.) for maximum product yield.

**Tech Stack:** Python 3.12+, Scrapling 0.5.0 (`Selector`), Patchright, BeautifulSoup4, Pytest, HTML/JS/CSS.

**Spec:** User request to restore missing products, update Facebook cookies, and make scraping more aggressive and effective using Scrapling.

## Global Constraints
- Preserve existing test suite pass rate (15/15 tests in `tests/test_parser.py` and `tests/test_post_copywriter.py`).
- Never lose live `source_posts.json` contract data; unify with catalog data cleanly.
- Ensure all dashboard exports (`public/index.html`, `index.html`, `data/reports/dashboard.html`) are updated and in sync.

## Review Focus
- Dashboard displays all 75+ products with functional affiliate links, Google Lens buttons, and images.
- Unfiltered and filtered views in dashboard correctly display items without blank screen bug.
- Scrapling `Selector` handles complex or obfuscated Facebook post DOM trees without crashes.
- Facebook session verification succeeds with the new cookies.

---

### Task 1: Unify Data Sources & Restore All 75+ Products

**Files:**
- Modify: `fb_winner_scout/storage.py`
- Modify: `fb_winner_scout/dashboard.py`
- Modify: `fb_winner_scout/__main__.py`
- Modify: `fb_winner_scout/pipeline.py`

- [ ] Add `load_all_dashboard_posts()` in `StorageManager` (`fb_winner_scout/storage.py`) to merge `viral_posts.json`, `catalog_posts.json`, and `source_posts.json` with field normalization.
- [ ] Fix frontend filtering in `fb_winner_scout/dashboard.py`:
  - Update `matchesPhysical` to recognize `(p.is_product || p.product_url || p.affiliate_url)`.
  - Remove `checked` attribute from `#physical-only` checkbox so it defaults to non-restrictive.
  - Ensure counts (`rx`, `cm`, `sh`, `clicks`) and image thumbnails display cleanly for both `SourcePost` and `ScrapedPost` models.
- [ ] Update `fb_winner_scout/__main__.py` and `fb_winner_scout/pipeline.py` so dashboard generation uses `load_all_dashboard_posts()`.
- [ ] Run `python -m fb_winner_scout dashboard` and verify generation of `public/index.html`, `index.html`, and `data/reports/dashboard.html` with 75 total products.

---

### Task 2: Verify Cookie Authentication & Session Health

**Files:**
- Modify: `cookies.json` (already updated)
- Verify: `fb_winner_scout/session.py`

- [ ] Verify `cookies.json` exists with all 9 valid Facebook cookies.
- [ ] Run `python -m fb_winner_scout verify-login` to confirm `logged-in` status.

---

### Task 3: Upgrade Crawler with Scrapling Selector & Fierce In-Group Search

**Files:**
- Modify: `fb_winner_scout/crawler.py`
- Modify: `fb_winner_scout/parser.py`
- Create: `tests/test_crawler_scrapling.py`

- [ ] Write tests in `tests/test_crawler_scrapling.py` testing post extraction using Scrapling `Selector`.
- [ ] Integrate Scrapling `Selector` into `crawler.py`:
  - Extract outer HTML of feed containers and parse with `scrapling.parser.Selector`.
  - Deep link regex search (`walmrt.us`, `amzn.to`, `amazon.com`, `fashlyst.com`, `aliexpress.com`, etc.) within both DOM attributes and text content.
  - Aggressive `scrollIntoView()` on the last feed container with smooth scrolling and intersection observer triggering.
- [ ] Support group keyword search (`/search/?q=walmart`, `amazon`, etc.) for high-intent viral product extraction.
- [ ] Run `python -m pytest` and ensure all tests pass.

---

### Task 4: End-to-End Verification

**Files:**
- Verify: `public/index.html`
- Verify: `tests/`

- [ ] Run full test suite (`python -m pytest`).
- [ ] Inspect dashboard HTML and confirm 75 posts rendered with images and working store buttons.
- [ ] Confirm git status and cleanliness.
