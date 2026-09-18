import os
import html
import time
import json
import urllib.request
import urllib.parse
from typing import Optional

class TelegramNotifier:
    """Sends clean Telegram notifications for run start, completion, and errors only."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None, dashboard_url: Optional[str] = None):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        self.dashboard_url = dashboard_url or os.environ.get("CLOUDFLARE_PAGES_URL", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str) -> bool:
        if not self.is_configured:
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "FBViralScout/1.0"}
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.status == 200
        except Exception as e:
            print(f"[Telegram Warning] Failed to send notification: {e}")
            return False

    def notify_run_started(self, groups_count: int, keywords_count: int, min_reactions: int) -> bool:
        """Sent when scraping starts."""
        now_str = time.strftime("%Y-%m-%d %I:%M %p")
        text = (
            "🚀 <b>بدء جولة سحب جديدة (Facebook Viral Scout)</b>\n\n"
            f"👥 <b>عدد الجروبات:</b> {groups_count}\n"
            f"🔑 <b>الكلمات المفتاحية:</b> {keywords_count}\n"
            f"🎯 <b>أدنى تفاعل:</b> +{min_reactions} لايك\n"
            f"⏰ <b>التوقيت:</b> {now_str}\n\n"
            "<i>جاري الفحص بالخلفية... سيصلك تقرير فوري عند الانتهاء.</i>"
        )
        return self.send_message(text)

    def notify_run_completed(self, collected_count: int, top_reactions: int = 0, top_post_url: str = "", total_groups: int = 0) -> bool:
        """Sent when scraping completes successfully."""
        now_str = time.strftime("%Y-%m-%d %I:%M %p")
        
        dash_link = ""
        if self.dashboard_url:
            dash_link = f"\n🌐 <a href='{self.dashboard_url}'><b>فتح الداش بورد على Cloudflare ↗</b></a>\n"

        text = (
            "✅ <b>اكتمل السحب بنجاح!</b>\n\n"
            f"📊 <b>إجمالي البوستات الفايرال:</b> {collected_count} منشور\n"
            f"👥 <b>الجروبات المفحوصة:</b> {total_groups}\n"
        )

        if top_reactions > 0:
            text += f"🔥 <b>أعلى بوست تفاعلاً:</b> 👍 {top_reactions:,} لايك\n"
            if top_post_url:
                text += f"🔗 <b>رابط البوست:</b> <a href='{top_post_url}'>عرض المنشور الأصلي</a>\n"

        text += dash_link
        text += f"\n⏰ <i>تم التحديث: {now_str}</i>"

        return self.send_message(text)

    def notify_error(self, error_message: str, step_context: str = "") -> bool:
        """Sent ONLY if an error occurs."""
        text = (
            "⚠️ <b>تنبيه: حدث خطأ أثناء السحب</b>\n\n"
            f"❌ <b>الخطأ:</b> <code>{html.escape(str(error_message)[:250])}</code>\n"
        )
        if step_context:
            text += f"📍 <b>المرحلة:</b> {html.escape(step_context)}\n"

        text += "\n<i>يرجى فحص صلاحية الكوكيز أو سجلات التشغيل.</i>"
        return self.send_message(text)
