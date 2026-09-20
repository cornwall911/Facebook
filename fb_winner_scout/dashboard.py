import json
from pathlib import Path
from typing import List
from fb_winner_scout.parser import ScrapedPost
from fb_winner_scout.config import ScoutConfig

def generate_html_dashboard(posts: List[ScrapedPost], config: ScoutConfig, filename: str = "dashboard.html") -> Path:
    """Generates an advanced, interactive HTML dashboard with sorting (highest likes/comments/shares), custom filters, Google Lens matching, and workflow management."""
    out_file = config.output_dir / "reports" / filename
    out_file.parent.mkdir(parents=True, exist_ok=True)

    posts_json = json.dumps([p.to_dict() for p in posts], ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Facebook Viral Scout Dashboard</title>
    <style>
        :root {{
            --bg-main: #0b0f19;
            --bg-card: #151d30;
            --border: #263352;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --purple: #a855f7;
            --badge-bg: #1e293b;
            --badge-text: #93c5fd;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Cairo", sans-serif; }}
        body {{ background-color: var(--bg-main); color: var(--text-primary); padding: 24px; direction: rtl; }}
        
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 16px; }}
        .title {{ font-size: 22px; font-weight: 700; display: flex; align-items: center; gap: 10px; color: #f1f5f9; }}
        .stats {{ display: flex; gap: 10px; flex-wrap: wrap; }}
        .stat-badge {{ background: var(--bg-card); border: 1px solid var(--border); padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 600; }}
        .stat-badge span {{ color: var(--success); font-weight: 700; margin-right: 4px; }}
        
        .top-toolbar {{ display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }}
        .toolbar-row {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
        
        .search-bar {{ flex: 1; min-width: 280px; max-width: 480px; padding: 11px 16px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-card); color: white; font-size: 14px; outline: none; }}
        .search-bar:focus {{ border-color: var(--accent); }}
        
        .btn-tips-toggle {{ background: linear-gradient(135deg, #f59e0b, #d97706); color: white; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 13px; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3); transition: transform 0.2s; }}
        .btn-tips-toggle:hover {{ transform: scale(1.02); }}

        /* Status Filters */
        .filter-tabs {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .filter-btn {{ background: #1e293b; color: #94a3b8; border: 1px solid var(--border); padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s; }}
        .filter-btn.active {{ background: var(--accent); color: white; border-color: var(--accent); }}
        .filter-btn:hover:not(.active) {{ background: #334155; color: white; }}

        /* New Advanced Controls Bar (Sort & Filters) */
        .controls-bar {{ background: #111827; border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }}
        .control-item {{ display: flex; align-items: center; gap: 8px; font-size: 13px; }}
        .control-item label {{ font-weight: 600; color: #94a3b8; white-space: nowrap; }}
        .select-control {{ background: var(--bg-card); color: #f1f5f9; border: 1px solid var(--border); border-radius: 6px; padding: 6px 12px; font-size: 12.5px; font-weight: 600; cursor: pointer; outline: none; }}
        .select-control:focus {{ border-color: var(--accent); }}
        
        .checkbox-control {{ display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: #cbd5e1; cursor: pointer; user-select: none; }}
        .checkbox-control input {{ cursor: pointer; accent-color: var(--accent); width: 16px; height: 16px; }}

        .showing-count {{ margin-right: auto; font-size: 12.5px; color: #94a3b8; font-weight: 600; }}
        .showing-count span {{ color: var(--accent); font-weight: 700; }}

        /* Floating Tips Modal */
        .tips-modal-overlay {{ position: fixed; inset: 0; background: rgba(0,0,0,0.75); backdrop-filter: blur(5px); display: none; align-items: center; justify-content: center; z-index: 1000; padding: 16px; }}
        .tips-modal {{ background: #111827; border: 1px solid #374151; width: 100%; max-width: 680px; border-radius: 16px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8); animation: fadeIn 0.25s ease-out; }}
        .tips-header {{ background: #0b1120; padding: 18px 24px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); }}
        .tips-title {{ font-size: 17px; font-weight: 700; color: #fbbf24; display: flex; align-items: center; gap: 8px; }}
        .close-btn {{ background: transparent; border: none; color: #94a3b8; font-size: 24px; cursor: pointer; line-height: 1; }}
        .close-btn:hover {{ color: white; }}
        .tips-body {{ padding: 22px; max-height: 75vh; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; font-size: 13.5px; line-height: 1.7; }}
        .tip-card {{ background: #1f2937; border-right: 4px solid var(--accent); padding: 14px 16px; border-radius: 8px; }}
        .tip-card.gold {{ border-right-color: var(--warning); }}
        .tip-card.green {{ border-right-color: var(--success); }}
        .tip-card.purple {{ border-right-color: var(--purple); }}
        .tip-card-title {{ font-weight: 700; margin-bottom: 6px; color: #f3f4f6; font-size: 14.5px; display: flex; align-items: center; gap: 6px; }}
        
        /* Grid and Cards */
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(370px, 1fr)); gap: 22px; }}
        .card {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s; }}
        .card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 30px -8px rgba(0,0,0,0.6); }}
        
        .card-header {{ padding: 14px 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; background: #0f172a; }}
        .badge {{ background: #1e3a8a; color: #bfdbfe; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; }}
        .metrics {{ display: flex; gap: 8px; font-size: 12.5px; font-weight: 700; direction: ltr; align-items: center; }}
        .ck {{ background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 2px 7px; border-radius: 6px; font-size: 11px; font-weight: 800; box-shadow: 0 2px 6px rgba(239, 68, 68, 0.4); letter-spacing: 0.5px; }}
        .rx {{ color: var(--success); }}
        .cm {{ color: #38bdf8; }}
        .sh {{ color: #fbbf24; }}
        
        .card-status-bar {{ padding: 8px 16px; background: #0b1120; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: center; font-size: 12px; }}
        .status-select {{ background: #1e293b; color: #e2e8f0; border: 1px solid #334155; border-radius: 6px; padding: 4px 8px; font-size: 11.5px; font-weight: 600; cursor: pointer; outline: none; }}
        
        .card-img-container {{ width: 100%; height: 230px; background: #070a12; display: flex; align-items: center; justify-content: center; overflow: hidden; position: relative; }}
        .card-img {{ width: 100%; height: 100%; object-fit: cover; cursor: pointer; transition: transform 0.3s; }}
        .card-img:hover {{ transform: scale(1.03); }}
        .no-img {{ color: var(--text-secondary); font-size: 13px; }}
        
        .thumbnails-row {{ display: flex; gap: 6px; padding: 6px 12px; background: #0b1120; overflow-x: auto; border-bottom: 1px solid #1e293b; }}
        .thumb {{ width: 44px; height: 44px; object-fit: cover; border-radius: 4px; cursor: pointer; border: 1.5px solid transparent; opacity: 0.65; transition: all 0.2s; }}
        .thumb.active, .thumb:hover {{ border-color: var(--accent); opacity: 1; }}

        .card-body {{ padding: 14px 16px; flex: 1; display: flex; flex-direction: column; gap: 10px; }}
        .author-info {{ font-size: 12px; color: #64748b; }}
        .author-info strong {{ color: #94a3b8; }}
        .caption-box {{ background: #0b1120; border: 1px solid #1e293b; padding: 10px 12px; border-radius: 8px; font-size: 13.5px; line-height: 1.6; color: #cbd5e1; max-height: 130px; overflow-y: auto; white-space: pre-line; direction: ltr; text-align: left; }}
        
        /* 1-to-5 Angles Drawer */
        .angles-drawer {{ display: none; background: #0f172a; border: 1px solid #334155; border-radius: 8px; padding: 12px; margin-top: 6px; flex-direction: column; gap: 10px; font-size: 12.5px; }}
        .angle-item {{ background: #1e293b; padding: 8px 10px; border-radius: 6px; border-right: 3px solid var(--purple); }}
        .angle-title {{ font-weight: 700; color: #e9d5ff; font-size: 11.5px; margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center; }}
        .angle-text {{ color: #cbd5e1; direction: ltr; text-align: left; font-size: 12px; line-height: 1.4; }}
        .angle-copy-btn {{ background: #374151; color: white; border: none; padding: 3px 8px; border-radius: 4px; font-size: 10.5px; cursor: pointer; }}
        .angle-copy-btn:hover {{ background: var(--purple); }}

        /* AI Short Caption Box */
        .ai-caption-box {{ background: #131b2e; border: 1.5px solid #6366f1; border-radius: 8px; padding: 10px 12px; margin-top: 6px; display: flex; flex-direction: column; gap: 6px; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.18); }}
        .ai-caption-header {{ display: flex; justify-content: space-between; align-items: center; font-size: 12px; font-weight: 700; color: #a5b4fc; }}
        .ai-caption-text {{ font-size: 13px; line-height: 1.5; color: #f1f5f9; direction: ltr; text-align: left; white-space: pre-line; }}
        .ai-copy-btn {{ background: #4f46e5; color: white; border: none; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; cursor: pointer; transition: background 0.2s; }}
        .ai-copy-btn:hover {{ background: #4338ca; }}

        /* Action Buttons */
        .card-actions-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--border); background: #0f172a; }}
        .btn {{ padding: 8px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; text-align: center; text-decoration: none; cursor: pointer; border: none; transition: background 0.2s, transform 0.1s; display: flex; align-items: center; justify-content: center; gap: 5px; }}
        .btn:active {{ transform: scale(0.98); }}
        .btn-primary {{ background: var(--accent); color: white; grid-column: span 1; }}
        .btn-lens {{ background: linear-gradient(135deg, #0ea5e9, #0284c7); color: white; grid-column: span 1; box-shadow: 0 2px 6px rgba(2, 132, 199, 0.3); text-decoration: none; }}
        .btn-lens:hover {{ background: linear-gradient(135deg, #38bdf8, #0ea5e9); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(2, 132, 199, 0.45); }}
        .img-lens-overlay {{ position: absolute; top: 10px; left: 10px; background: rgba(15, 23, 42, 0.88); backdrop-filter: blur(5px); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.45); border-radius: 20px; padding: 4px 10px; font-size: 11px; font-weight: 700; cursor: pointer; display: flex; align-items: center; gap: 5px; transition: all 0.2s ease; z-index: 10; text-decoration: none; box-shadow: 0 3px 10px rgba(0,0,0,0.6); }}
        .img-lens-overlay:hover {{ background: #0284c7; color: #ffffff; border-color: #38bdf8; transform: scale(1.05); }}
        .btn-sheet {{ background: #059669; color: white; grid-column: span 1; }}
        .btn-sheet:hover {{ background: #047857; }}
        .btn-affiliate {{ background: #059669; color: white; grid-column: span 1; text-decoration: none; }}
        .btn-affiliate:hover {{ background: #047857; }}
        .btn-amazon {{ background: #ea580c; color: white; grid-column: span 1; text-decoration: none; }}
        .btn-amazon:hover {{ background: #c2410c; }}
        .prod-badge {{ background: #064e3b; color: #34d399; border: 1px solid #059669; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }}
        .score-badge {{ background: #78350f; color: #fde047; border: 1px solid #b45309; padding: 3px 6px; border-radius: 6px; font-size: 11px; font-weight: 700; }}
        .btn-angles-toggle {{ background: #7c3aed; color: white; grid-column: span 1; }}
        .btn-angles-toggle:hover {{ background: #6d28d9; }}
        .btn-secondary {{ background: #334155; color: #cbd5e1; grid-column: span 2; font-size: 11.5px; padding: 6px; }}
        .btn-secondary:hover {{ background: #475569; color: white; }}

        .toast {{ position: fixed; bottom: 24px; left: 24px; background: var(--success); color: white; padding: 12px 20px; border-radius: 8px; font-weight: 700; font-size: 13px; display: none; box-shadow: 0 8px 24px rgba(0,0,0,0.5); z-index: 2000; animation: fadeIn 0.2s ease-out; }}

        @keyframes fadeIn {{ from {{ opacity: 0; transform: scale(0.96); }} to {{ opacity: 1; transform: scale(1); }} }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">🚀 لوحة تحكم سكاوت المنتجات الفايرال (Facebook Viral Scout)</div>
        <div class="stats">
            <div class="stat-badge">إجمالي البوستات: <span id="total-count">0</span></div>
            <div class="stat-badge">المعروض الآن: <span id="visible-count">0</span></div>
            <div class="stat-badge">أقل تفاعل للسكاوت: <span>{config.min_reactions}+</span></div>
        </div>
    </div>

    <div class="top-toolbar">
        <div class="toolbar-row">
            <input type="text" id="search" class="search-bar" placeholder="🔍 ابحث بالمنتج، الكلمة المفتاحية، أو نص الكابشن..." oninput="applyFilters()">
            <button class="btn-tips-toggle" onclick="toggleTipsModal(true)">💡 دليل أسرار النشر والـ 10,000 كليك (اضغط هنا)</button>
        </div>

        <!-- Row 1: Workflow Status Tabs -->
        <div class="toolbar-row">
            <span style="font-size: 12.5px; color: #94a3b8; font-weight: 600;">مراحل العمل:</span>
            <div class="filter-tabs">
                <button class="filter-btn active" onclick="setStatusFilter('all', this)">الكل (<span id="cnt-all">0</span>)</button>
                <button class="filter-btn" id="filter-top-clicks" onclick="toggleClicksOnly(this)" style="border-color: #ef4444; color: #f87171;">🔥 أبطال المبيعات (+100 Clicks)</button>
                <button class="filter-btn" onclick="setStatusFilter('new', this)">⚪ جديد (<span id="cnt-new">0</span>)</button>
                <button class="filter-btn" onclick="setStatusFilter('sent', this)">🟡 أُرسل لأحمد عادل (<span id="cnt-sent">0</span>)</button>
                <button class="filter-btn" onclick="setStatusFilter('ready', this)">🟢 جاهز للنشر (<span id="cnt-ready">0</span>)</button>
                <button class="filter-btn" onclick="setStatusFilter('published', this)">🚀 تم النشر (<span id="cnt-published">0</span>)</button>
            </div>
        </div>

        <!-- Row 2: Advanced Controls (Sort by Reactions/Comments/Shares, Min Likes, Niche, Photos Only) -->
        <div class="controls-bar">
            <div class="control-item">
                <label for="sort-select">⚡ الترتيب:</label>
                <select id="sort-select" class="select-control" onchange="applyFilters()">
                    <option value="reactions_desc">🔥 الأعلى تفاعلاً (افتراضي)</option>
                    <option value="clicks_desc">💎 الأكثر نقرات ومبيعات (+100 Clicks)</option>
                    <option value="comments_desc">💬 الأكثر تعليقات (Link Requests)</option>
                    <option value="shares_desc">🔁 الأكثر مشاركة (Viral Shares)</option>
                    <option value="reactions_asc">📉 الأقل تفاعلاً</option>
                    <option value="default">🕒 الترتيب الأصلي</option>
                </select>
            </div>

            <div class="control-item">
                <label for="min-rx-select">🎯 أدنى تفاعل:</label>
                <select id="min-rx-select" class="select-control" onchange="applyFilters()">
                    <option value="0">الكل (بدون حد أدنى)</option>
                    <option value="2">⚡ +2 لايكات (صاحبة النقرات العالية)</option>
                    <option value="5">👍 +5 لايكات</option>
                    <option value="10">👍 +10 لايكات</option>
                    <option value="25">⭐ +25 لايك</option>
                    <option value="50">⚡ +50 لايك</option>
                    <option value="100">🔥 +100 لايك</option>
                    <option value="250">🚀 +250 لايك (Mega-Viral)</option>
                    <option value="500">👑 +500 لايك (Super-Winners)</option>
                </select>
            </div>

            <div class="control-item">
                <label for="platform-select">🌐 المنصة:</label>
                <select id="platform-select" class="select-control" onchange="applyFilters()">
                    <option value="all">🌐 الكل (Facebook + Pinterest)</option>
                    <option value="facebook">👥 فيسبوك فقط (Facebook Groups)</option>
                    <option value="pinterest">📌 بينتيريست فقط (Pinterest Finds)</option>
                </select>
            </div>

            <div class="control-item">
                <label for="keyword-select">🏷️ النيش / الكلمة:</label>
                <select id="keyword-select" class="select-control" onchange="applyFilters()">
                    <option value="all">كل الكلمات والنيشات</option>
                </select>
            </div>

            <div class="control-item">
                <label class="checkbox-control">
                    <input type="checkbox" id="physical-only" checked onchange="applyFilters()">
                    <span>📦 منتجات فيزيائية فقط</span>
                </label>
            </div>

            <div class="control-item">
                <label class="checkbox-control">
                    <input type="checkbox" id="has-img-only" onchange="applyFilters()">
                    <span>🖼️ بوستات بصور فقط</span>
                </label>
            </div>

            <div class="showing-count">
                عرض <span id="filtered-num">0</span> من أصل <span id="total-num">0</span>
            </div>
        </div>
    </div>

    <div class="grid" id="posts-grid"></div>

    <!-- Floating Tips Modal -->
    <div class="tips-modal-overlay" id="tips-modal" onclick="if(event.target === this) toggleTipsModal(false)">
        <div class="tips-modal">
            <div class="tips-header">
                <div class="tips-title">💡 دليل أسرار مضاعفة الكليكات والوصول لـ 10,000 كليك</div>
                <button class="close-btn" onclick="toggleTipsModal(false)">&times;</button>
            </div>
            <div class="tips-body">
                <div class="tip-card gold">
                    <div class="tip-card-title">⏰ 1. أنسب مواعيد النشر (مضبوطة بتوقيت مصر):</div>
                    <div>جمهور أمريكا بيكون متفاعل في نافذتين أساسيتين يومياً:</div>
                    <ul style="margin-right: 20px; margin-top: 6px;">
                        <li><strong>نافذة الظهيرة (وقت الغداء بأمريكا):</strong> من <strong>5:30 مساءً إلى 7:30 مساءً</strong> بتوقيت مصر.</li>
                        <li><strong>النافذة الذهبية (ذروة السهرة وأعلى كليكات):</strong> من <strong>1:30 صباحاً إلى 4:00 فجراً</strong> بتوقيت مصر.</li>
                    </ul>
                </div>

                <div class="tip-card green">
                    <div class="tip-card-title">🚀 2. قاعدة "المنتج الفائز لا يموت" (The 1-to-5 Rule):</div>
                    <div>إذا لقيت منتج ضرب في جروب وجاب 500+ كليك، ده كنز! فوراً خده وانشره في <strong>4 أو 5 جروبات تانية متصلة</strong> بنفس النيش (مثلاً: منتج تخييم انشره في جروبات Vanlife, RV, Dog Owners, Offroad). غير فقط الصورة الأولى وعدّل أول سطرين في الكابشن لمنع نظام كشف المحتوى المكرر (استخدم زر زوايا الكابشن 1-to-5 الموجود أسفل كل كارت).</div>
                </div>

                <div class="tip-card gold">
                    <div class="tip-card-title">🔄 3. سر إنعاش البوست بعد 24 ساعة (The Bump Trick):</div>
                    <div>بعد ما تنشر البوست ويعدي عليه 24 ساعة ويبدأ ينام، ادخل بحسابك التاني في Incogniton واكتب كومنت استفساري زي: <em>"Does this fit standard cabinets?"</em> أو <em>"Where did you order this from?"</em>، وادخل رد عليه من حسابك الأساسي. ده هيرفع البوست لأعلى الجروب فوراً ويجيبلك موجة كليكات تانية مجانية!</div>
                </div>

                <div class="tip-card purple">
                    <div class="tip-card-title">💬 4. منجم الكليكات في الخاص (The DM Goldmine):</div>
                    <div>بدل ما تنزل الرابط فوراً لـ 20 واحد في الكومنتات وفيسبوك يحظرك: رد عليهم في الكومنت: <em>"Sent you the direct link in your DM check your message requests! 😊"</em>، ثم ابعته في ماسنجر. معدل فتح الرسائل في الماسنجر بيتجاوز <strong>85%</strong> وبيمنع المنافسين في الجروب يسرقوا كليكاتك.</div>
                </div>

                <div class="tip-card">
                    <div class="tip-card-title">🚫 5. الكلمات الممنوعة في الكابشن (Anti-Spam Copy):</div>
                    <div>إياك تكتب: <em>Amazon, Discount, Buy now, Sale, Shop, Link, Coupon</em>. وجود الكلمات دي بيخلي البوست يتعلق في انتظار موافقة الأدمن أو خوارزمية فيسبوك تقلل وصوله 90%. استخدم دائماً أسلوب تجربة شخصية طبيعية: <em>"Finally found a fix for..."</em> أو <em>"Best $15 I spent this year..."</em>.</div>
                </div>

                <div class="tip-card">
                    <div class="tip-card-title">🛡️ 6. فواصل الأمان وإدارة الحسابات في Incogniton:</div>
                    <div>انشر من <strong>1 إلى 2 بوست يومياً فقط</strong> لكل بروفايل في Incogniton. سيب فاصل <strong>20 إلى 30 دقيقة</strong> بين البوستات، وتصفح الجروب واعمل لايك طبيعي قبل النشر بدقائق عشان البروفايل يفضل موثوق وميتحظرش.</div>
                </div>

                <div class="tip-card">
                    <div class="tip-card-title">📊 7. تتبع أرباح كل جروب (Sub-IDs مع أحمد عادل):</div>
                    <div>اطلب من أحمد عادل يضيف لك Sub-ID لكل رابط (مثلاً: <code>?subid=rv_group1</code>). بكده هتعرف بدقة مين الجروبات اللي بتعمل 80% من الكليكات والمبيعات وتركز وقتك عليها!</div>
                </div>
            </div>
        </div>
    </div>

    <div id="toast" class="toast">تمت العملية بنجاح! 📋</div>

    <script>
        const rawPosts = {posts_json};
        let currentStatusFilter = 'all';

        function toggleTipsModal(show) {{
            document.getElementById('tips-modal').style.display = show ? 'flex' : 'none';
        }}

        function showToast(msg) {{
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.style.display = 'block';
            setTimeout(() => {{ t.style.display = 'none'; }}, 2500);
        }}

        function getPostStatus(postId) {{
            return localStorage.getItem('status_' + postId) || 'new';
        }}

        function setPostStatus(postId, status) {{
            localStorage.setItem('status_' + postId, status);
            updateCounters();
            applyFilters();
        }}

        function updateCounters() {{
            const counts = {{ all: rawPosts.length, new: 0, sent: 0, ready: 0, published: 0 }};
            rawPosts.forEach(p => {{
                const st = getPostStatus(p.post_id);
                if (counts[st] !== undefined) counts[st]++;
            }});
            document.getElementById('total-count').innerText = counts.all;
            document.getElementById('total-num').innerText = counts.all;
            document.getElementById('cnt-all').innerText = counts.all;
            document.getElementById('cnt-new').innerText = counts.new;
            document.getElementById('cnt-sent').innerText = counts.sent;
            document.getElementById('cnt-ready').innerText = counts.ready;
            document.getElementById('cnt-published').innerText = counts.published;
        }}

        function setStatusFilter(status, btn) {{
            currentStatusFilter = status;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');
            applyFilters();
        }}

        function populateKeywordDropdown() {{
            const kwSelect = document.getElementById('keyword-select');
            const uniqueKws = [...new Set(rawPosts.map(p => p.keyword).filter(Boolean))];
            uniqueKws.forEach(kw => {{
                const opt = document.createElement('option');
                opt.value = kw;
                opt.innerText = kw;
                kwSelect.appendChild(opt);
            }});
        }}

        let clicksOnlyFilter = false;
        function toggleClicksOnly(btn) {{
            clicksOnlyFilter = !clicksOnlyFilter;
            if (clicksOnlyFilter) {{
                btn.classList.add('active');
                btn.style.background = '#ef4444';
                btn.style.color = '#ffffff';
            }} else {{
                btn.classList.remove('active');
                btn.style.background = '';
                btn.style.color = '#f87171';
            }}
            applyFilters();
        }}

        function applyFilters() {{
            const q = document.getElementById('search').value.toLowerCase();
            const sortVal = document.getElementById('sort-select').value;
            const minRx = parseInt(document.getElementById('min-rx-select').value) || 0;
            const kwFilter = document.getElementById('keyword-select').value;
            const hasImgOnly = document.getElementById('has-img-only').checked;
            const physicalOnly = document.getElementById('physical-only') ? document.getElementById('physical-only').checked : false;

            const platformFilter = document.getElementById('platform-select') ? document.getElementById('platform-select').value : 'all';

            let filtered = rawPosts.filter(p => {{
                const st = getPostStatus(p.post_id);
                const matchesStatus = (currentStatusFilter === 'all') || (st === currentStatusFilter);
                const matchesClicks = !clicksOnlyFilter || (p.clicks_count && p.clicks_count >= 100);
                const matchesQuery = !q || 
                    (p.keyword && p.keyword.toLowerCase().includes(q)) || 
                    (p.caption && p.caption.toLowerCase().includes(q)) ||
                    (p.author && p.author.toLowerCase().includes(q));
                
                const isPin = (p.group_id && p.group_id.toLowerCase().includes('pinterest')) || (p.keyword && p.keyword.toLowerCase().includes('pinterest'));
                const matchesPlatform = (platformFilter === 'all') ||
                    (platformFilter === 'pinterest' && isPin) ||
                    (platformFilter === 'facebook' && !isPin);

                const matchesMinRx = (p.reactions_count || 0) >= minRx;
                const matchesKw = (kwFilter === 'all') || (p.keyword === kwFilter);
                
                const imgs = p.image_urls ? p.image_urls.split('; ').filter(Boolean) : [];
                const matchesImg = !hasImgOnly || imgs.length > 0;
                const matchesPhysical = !physicalOnly || (p.is_product && imgs.length > 0);

                return matchesStatus && matchesClicks && matchesQuery && matchesPlatform && matchesMinRx && matchesKw && matchesImg && matchesPhysical;
            }});

            // Apply Sorting
            if (sortVal === 'clicks_desc') {{
                filtered.sort((a, b) => (b.clicks_count || 0) - (a.clicks_count || 0));
            }} else if (sortVal === 'reactions_desc') {{
                filtered.sort((a, b) => (b.reactions_count || 0) - (a.reactions_count || 0));
            }} else if (sortVal === 'comments_desc') {{
                filtered.sort((a, b) => (b.comments_count || 0) - (a.comments_count || 0));
            }} else if (sortVal === 'shares_desc') {{
                filtered.sort((a, b) => (b.shares_count || 0) - (a.shares_count || 0));
            }} else if (sortVal === 'reactions_asc') {{
                filtered.sort((a, b) => (a.reactions_count || 0) - (b.reactions_count || 0));
            }}

            document.getElementById('visible-count').innerText = filtered.length;
            document.getElementById('filtered-num').innerText = filtered.length;

            renderPosts(filtered);
        }}

        function renderPosts(posts) {{
            const grid = document.getElementById('posts-grid');
            grid.innerHTML = '';
            if (posts.length === 0) {{
                if (rawPosts.length === 0) {{
                    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 60px 24px; color: #94a3b8; font-size: 16px;"><div style="font-size: 40px; margin-bottom: 12px;">⏳</div><strong>الداش بورد نظيفة وجاهزة تماماً!</strong><br><span style="font-size: 13px; color: #64748b; margin-top: 6px; display: block;">سيتم إضافة المنشورات الفايرال تلقائياً بمجرد تشغيل دورة السحب.</span></div>';
                }} else {{
                    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 48px; color: #64748b; font-size: 15px;">لا توجد بوستات تطابق خيارات الترتيب والفلترة المحددة.</div>';
                }}
                return;
            }}

            posts.forEach(p => {{
                const card = document.createElement('div');
                card.className = 'card';
                
                const imgs = p.image_urls ? p.image_urls.split('; ').filter(Boolean) : [];
                const firstImg = imgs.length > 0 ? imgs[0] : null;
                const status = getPostStatus(p.post_id);

                // Google Lens direct search URL
                const lensUrl = firstImg ? `https://lens.google.com/uploadbyurl?url=${{encodeURIComponent(firstImg)}}` : null;

                // Build thumbnails
                let thumbsHtml = '';
                if (imgs.length > 1) {{
                    thumbsHtml = `<div class="thumbnails-row">` + 
                        imgs.map((img, idx) => `<img src="${{img}}" class="thumb ${{idx===0?'active':''}}" onclick="changeMainImage('${{p.post_id}}', '${{img}}', this)">`).join('') + 
                        `</div>`;
                }}

                card.innerHTML = `
                    <div class="card-header">
                        <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                            ${{(p.clicks_count && p.clicks_count >= 100) ? `<span class="badge" style="background:#7f1d1d;color:#fecaca;border:1px solid #ef4444;font-weight:800;">🏆 فائز مثبت (+100 Clicks)</span>` : ''}}
                            ${{(p.group_id && p.group_id.includes('Pinterest')) ? `<span class="badge" style="background:#be185d;color:#fdf2f8;border:1px solid #f43f5e;">📌 بينتيريست</span>` : `<span class="badge">${{escapeHtml(p.keyword || 'Viral Post')}}</span>`}}
                            ${{p.is_product ? `<span class="prod-badge">📦 ${{escapeHtml(p.product_category || 'منتج فيزيائي')}}</span>` : ''}}
                            ${{p.winner_score ? `<span class="score-badge">⭐ ${{p.winner_score}}/100</span>` : ''}}
                            ${{(p.caption && /comment|below|first\\s*comm/i.test(p.caption)) ? `<span class="badge" style="background:#312e81;color:#c7d2fe;border:1px solid #6366f1;">💬 اللينك في التعليقات</span>` : ''}}
                        </div>
                        <div class="metrics">
                            ${{p.clicks_count ? `<span class="ck" title="عدد النقرات الفعلية المثبتة">🔥 ${{p.clicks_count.toLocaleString()}} Clicks</span>` : ''}}
                            <span class="rx" title="عدد اللايكات والتفاعلات">👍 ${{p.reactions_count.toLocaleString()}}</span>
                            <span class="cm" title="عدد التعليقات">💬 ${{p.comments_count.toLocaleString()}}</span>
                            <span class="sh" title="عدد المشاركات">🔁 ${{p.shares_count.toLocaleString()}}</span>
                        </div>
                    </div>

                    <div class="card-status-bar">
                        <span style="color: #94a3b8;">حالة المنشور:</span>
                        <select class="status-select ${{status}}" onchange="setPostStatus('${{p.post_id}}', this.value)">
                            <option value="new" ${{status==='new'?'selected':''}}>⚪ جديد (New)</option>
                            <option value="sent" ${{status==='sent'?'selected':''}}>🟡 أُرسل لأحمد عادل</option>
                            <option value="ready" ${{status==='ready'?'selected':''}}>🟢 الرابط جاهز للنشر</option>
                            <option value="published" ${{status==='published'?'selected':''}}>🚀 تم النشر في الجروبات</option>
                        </select>
                    </div>

                    <div class="card-img-container">
                        ${{firstImg ? `
                            <a id="lens-overlay-${{p.post_id}}" href="${{lensUrl}}" target="_blank" class="img-lens-overlay" title="ابحث عن هذا المنتج وسعره بالصورة في Google Lens">
                                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M3 7V5a2 2 0 0 1 2-2h2"></path><path d="M17 3h2a2 2 0 0 1 2 2v2"></path><path d="M21 17v2a2 2 0 0 1-2 2h-2"></path><path d="M7 21H5a2 2 0 0 1-2-2v-2"></path></svg>
                                <span>Google Lens</span>
                            </a>
                            <img id="main-img-${{p.post_id}}" src="${{firstImg}}" class="card-img" onerror="this.style.display='none'">
                        ` : '<div class="no-img">لا توجد صورة</div>'}}
                    </div>
                    ${{thumbsHtml}}

                    <div class="card-body">
                        <div class="author-info">الناشر: <strong>${{escapeHtml(p.author || 'عضو')}}</strong> | في جروب: ${{escapeHtml(p.group_id === 'RVhackcamp' ? 'RV Camping & Ideas' : (p.group_id || 'عام'))}}</div>
                        <div class="caption-box">${{escapeHtml(p.caption || 'No text')}}</div>
                        
                        ${{p.generated_caption ? `
                        <div class="ai-caption-box">
                            <div class="ai-caption-header">
                                <span>✍️ كابشن تسويقي جاهز للنشر (Short & High-Converting):</span>
                                <button class="ai-copy-btn" onclick="copyCaption('${{encodeURIComponent(p.generated_caption)}}')">📋 نسخ</button>
                            </div>
                            <div class="ai-caption-text">${{escapeHtml(p.generated_caption)}}</div>
                        </div>
                        ` : ''}}

                        <!-- 1-to-5 Angles Drawer -->
                        <div class="angles-drawer" id="angles-${{p.post_id}}">
                            <div class="angle-item">
                                <div class="angle-title">
                                     <span>🎯 زاوية حل المشكلة (Pain Relief)</span>
                                    <button class="angle-copy-btn" onclick="copyText('Honestly didn\\'t expect this to work so well, but it literally solved the problem during our last trip! Worth every penny. Anyone else using one?')">📋 نسخ</button>
                                </div>
                                <div class="angle-text">"Honestly didn't expect this to work so well, but it literally solved the problem during our last trip! Worth every penny. Anyone else using one?"</div>
                            </div>
                            <div class="angle-item">
                                <div class="angle-title">
                                    <span>🔍 زاوية الاكتشاف والترشيح (Social Discovery)</span>
                                    <button class="angle-copy-btn" onclick="copyText('Someone in another group recommended this a few weeks ago and I finally got one. Absolute game changer! Dropping the link in the comments if anyone wants it.')">📋 نسخ</button>
                                </div>
                                <div class="angle-text">"Someone in another group recommended this a few weeks ago and I finally got one. Absolute game changer! Dropping the link in the comments if anyone wants it."</div>
                            </div>
                            <div class="angle-item">
                                <div class="angle-title">
                                    <span>💬 زاوية الفضول والتفاعل (Curiosity Hook)</span>
                                    <button class="angle-copy-btn" onclick="copyText('Why did nobody tell me this existed before?! Found this gadget last weekend and it completely upgraded my setup. Comment if you need details!')">📋 نسخ</button>
                                </div>
                                <div class="angle-text">"Why did nobody tell me this existed before?! Found this gadget last weekend and it completely upgraded my setup. Comment if you need details!"</div>
                            </div>
                        </div>
                    </div>

                    <div class="card-actions-grid">
                        ${{p.generated_caption ? 
                            `<button class="btn btn-primary" onclick="copyCaption('${{encodeURIComponent(p.generated_caption)}}')">📋 نسخ كابشن النشر</button>` : 
                            `<button class="btn btn-primary" onclick="copyCaption('${{encodeURIComponent(p.caption)}}')">📋 نسخ الكابشن الأصلي</button>`
                        }}
                        ${{lensUrl ? `<a id="lens-btn-${{p.post_id}}" href="${{lensUrl}}" target="_blank" class="btn btn-lens" title="البحث الفوري عن المنتج في Google Lens لمعرفة اسمه وسعره بدقة">🔍 بحث بالصورة (Google Lens)</a>` : `<button class="btn btn-lens" disabled style="opacity:0.4;">🔍 لا توجد صورة</button>`}}
                        ${{p.affiliate_url ? `<a href="${{p.affiliate_url}}" target="_blank" class="btn btn-affiliate">🔗 رابط المنتج المعروض</a>` : ''}}
                        <a href="https://www.amazon.com/s?k=${{encodeURIComponent(p.amazon_query || p.keyword || 'rv gadget')}}" target="_blank" class="btn btn-amazon">🛒 بحث في أمازون</a>
                        <button class="btn btn-sheet" onclick="copySheetRow('${{p.post_id}}')">📑 نسخ لشيت أحمد</button>
                        <button class="btn btn-angles-toggle" onclick="toggleAngles('${{p.post_id}}')">✨ زوايا (1-to-5)</button>
                        <a href="${{p.post_url}}" target="_blank" class="btn btn-secondary">🔗 فتح البوست الأصلي في فيسبوك</a>
                    </div>
                `;
                grid.appendChild(card);
            }});
        }}

        function changeMainImage(postId, imgUrl, thumbElem) {{
            const main = document.getElementById('main-img-' + postId);
            if (main) main.src = imgUrl;
            const parent = thumbElem.parentElement;
            parent.querySelectorAll('.thumb').forEach(t => t.classList.remove('active'));
            thumbElem.classList.add('active');

            const encoded = encodeURIComponent(imgUrl);
            const newLensUrl = `https://lens.google.com/uploadbyurl?url=${{encoded}}`;
            const btn = document.getElementById('lens-btn-' + postId);
            if (btn) btn.href = newLensUrl;
            const overlay = document.getElementById('lens-overlay-' + postId);
            if (overlay) overlay.href = newLensUrl;
        }}

        function toggleAngles(postId) {{
            const el = document.getElementById('angles-' + postId);
            if (el) {{
                el.style.display = (el.style.display === 'flex') ? 'none' : 'flex';
            }}
        }}

        function escapeHtml(str) {{
            if (!str) return '';
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
        }}

        function copyText(text) {{
            navigator.clipboard.writeText(text).then(() => {{
                showToast("تم نسخ الزاوية بنجاح! 📋");
            }});
        }}

        function copyCaption(encoded) {{
            const text = decodeURIComponent(encoded);
            navigator.clipboard.writeText(text).then(() => {{
                showToast("تم نسخ الكابشن بنجاح! 📋");
            }});
        }}

        function copySheetRow(postId) {{
            const p = rawPosts.find(item => item.post_id === postId);
            if (!p) return;
            const imgs = p.image_urls ? p.image_urls.split('; ').filter(Boolean) : [];
            const firstImg = imgs.length > 0 ? imgs[0] : '';
            const cleanCap = (p.caption || '').replace(/[\\r\\n\\t]+/g, ' ').substring(0, 150);
            
            // Format TSV row for Excel / Google Sheets
            const rowTsv = `${{p.keyword || 'Product'}}\\t${{p.post_url}}\\t${{p.reactions_count}}\\t${{firstImg}}\\t${{cleanCap}}\\tجاهز لطلب الرابط`;
            
            navigator.clipboard.writeText(rowTsv).then(() => {{
                showToast("تم نسخ صف الإكسيل! افتح شيت أحمد عادل واضغط Ctrl+V 📊");
            }});
        }}

        // Initialization
        populateKeywordDropdown();
        updateCounters();
        applyFilters();
    </script>
</body>
</html>
"""

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    # Also save to public/index.html and root index.html for seamless Cloudflare Pages deployment
    public_file = Path("public/index.html")
    public_file.parent.mkdir(parents=True, exist_ok=True)
    with open(public_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    root_file = Path("index.html")
    with open(root_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[Dashboard] Generated interactive dashboard at: {out_file}, {public_file}, & {root_file}")
    return out_file

