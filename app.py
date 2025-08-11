from flask import Flask, redirect, request, session, url_for, jsonify
import requests
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # ضروري للجلسات

# معلومات التطبيق - استبدلهم بقيمك من Webex Developer Portal
CLIENT_ID = "Cd2d3a9e3f697b9f276b649c7963816e83ee21f39ef7dea85a176056f2a71ad09"
CLIENT_SECRET = "a50e64377c72337e9e924a460e303139bc45e4feb514616c5296eb29f5fd5678"
REDIRECT_URI = "https://7ce543dc8f44.ngrok-free.app/callback"

# صفحة رئيسية تعرض واجهة HTML (ممكن تغيرها حسب الحاجة)
@app.route("/")
def index():
    return app.send_static_file("index.html")

# رابط تسجيل الدخول: يوجه المستخدم لصفحة تسجيل الدخول في Webex
@app.route("/login")
def login():
    auth_url = (
        "https://webexapis.com/v1/authorize?"
        f"client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
        "&scope=spark:all&state=xyz"
    )
    return redirect(auth_url)

# Webex يعيد التوجيه هنا بعد تسجيل الدخول مع كود التفويض
@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "No code provided", 400

    # تبادل الكود للحصول على توكن الوصول
    token_url = "https://webexapis.com/v1/access_token"
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    r = requests.post(token_url, data=data)
    if r.status_code != 200:
        return f"Failed to get token: {r.text}", 400

    token_data = r.json()
    # حفظ التوكن في الجلسة
    session["access_token"] = token_data["access_token"]

    return redirect("/app")  # توجيه المستخدم لواجهة التطبيق

# صفحة التطبيق بعد تسجيل الدخول
@app.route("/app")
def app_page():
    return app.send_static_file("app.html")

# API لجلب الرومات (الغرف)
@app.route("/api/rooms")
def get_rooms():
    token = session.get("access_token")
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get("https://webexapis.com/v1/rooms", headers=headers)
    if r.status_code != 200:
        return jsonify({"error": "Failed to get rooms"}), 500

    return jsonify(r.json())

# API لإرسال رسالة
@app.route("/api/send_message", methods=["POST"])
def send_message():
    token = session.get("access_token")
    if not token:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.json
    room_id = data.get("roomId")
    text = data.get("text")
    if not room_id or not text:
        return jsonify({"error": "Missing parameters"}), 400

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    msg_data = {"roomId": room_id, "text": text}

    r = requests.post("https://webexapis.com/v1/messages", json=msg_data, headers=headers)
    if r.status_code != 200 and r.status_code != 202:
        return jsonify({"error": f"Failed to send message: {r.text}"}), 500

    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(debug=True)
