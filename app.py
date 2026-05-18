from flask import Flask, request, jsonify
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
import openai
import threading
import time
from dotenv import load_dotenv
import os

# === ENVIRONMENT VARIABLES ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
HF_MODEL = os.getenv("HF_MODEL")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
API_URL = "https://router.huggingface.co/together/v1/chat/completions"

#HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
# === Initialize Firebase Admin SDK ===
cred = credentials.Certificate('firebase-adminsdk.json')
firebase_admin.initialize_app(cred)
firestore_db = firestore.client()

# === Flask Setup ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Flask server is running. Telegram bot is polling in background."






    print(response.text)
    return response.json()
# === Hugging Face Inference ===
def extract_location_status(text):
    prompt = f"""
استخرج الحالة للمكان من الجملة العربية التالية. أعد اسم المكان كما هو في النص، ولا تعدله.
استخدم هذا التنسيق في السطر الواحد فقط: "اسم المكان - الحالة"
✅ = مفتوح، ❌ = مغلق
وفي حال كانت الحالة مسكر او مسكرة يعني الحالة مغلق
وفي حالة كانت سالكة يعني الحالة مفتوح
وفي حالة كان حالة مثل أزمة خانفةاو أزمة او مأزم تكون الحالة أزمة
وفقط اسم المكان بدون اضافات مثل خانقة او مدينة او بلدة او قرية او حي
مثلا مدينة عزون ازمة خانقة تكون الحالة أزمةو اسم المكان عزون
في حال كات الحالة مسكر او مسكرة يعني الحالة مغلق
الجملة:
{text}

أجب فقط بهذا الشكل:
اسم المكان -  الحالة
مثال: جيوس - الحالة
"""

    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "model": HF_MODEL
    }
   # print(payload)

    response = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {HF_API_KEY}"},
        json=payload  # <-- Use json, not data
    )
   
    if response.status_code != 200:
        print(f"❌ Error from Hugging Face: {response.text}")
        return {'location': '', 'status': 'غير محدد', 'raw_output': response.text}

    result = response.json()

    # Extract generated text from the chat completion format
    generated = ""
    if "choices" in result and result["choices"]:
        generated = result["choices"][0]["message"]["content"]
    else:
        print("❌ Unexpected response format from model")
        return {'location': '', 'status': 'غير محدد', 'raw_output': str(result)}

    parts = generated.split('-')
    if len(parts) == 2:
        location = parts[0].strip()
        status = parts[1].strip()
    else:
        location = ""
        status = generated.strip()
   
    print(f"📍 Extracted Location: {location}, Status: {status}")
    return {
        "location": location,
        "status": status,
        "raw_output": generated
    }
    
    

# === Firestore Logic ===
def update_firestore_status(location_name, status_value, msg_timestamp=None):
    try:
        gate_collection = firestore_db.collection('Gate')
        docs = gate_collection.stream()

        matched = False

        for doc in docs:
            doc_data = doc.to_dict()
            name_ar = doc_data.get('nameAr', '').strip()
            name_en = doc_data.get('nameEn', '').strip()
            location_name = location_name.strip()

            if location_name == name_ar or location_name == name_en:
                update_data = {'stutes': status_value}
                if msg_timestamp:
                    # Convert Unix timestamp to Firestore Timestamp (timezone-aware)
                    update_data['timestamp'] = datetime.fromtimestamp(msg_timestamp, timezone.utc)
                doc.reference.update(update_data)
                print(f"✅ Updated document '{doc.id}' with status: {status_value} and timestamp: {msg_timestamp}")
                matched = True

        if not matched:
            print(f"⚠️ No document found with nameAr or nameEn matching: {location_name}")

    except Exception as e:
        print(f"🔥 Error updating Firestore: {e}")

# === Telegram Polling Loop ===
def telegram_polling_loop():
    print("🤖 Telegram polling started...")

    # Get the last update ID to skip old messages
    offset = None
    try:
        response = requests.get(f"{TELEGRAM_API_URL}/getUpdates")
        data = response.json()
        updates = data.get("result", [])
        if updates:
            offset = updates[-1]["update_id"] + 1
    except Exception as e:
        print("⚠️ Initial fetch error:", e)
        offset = None

    while True:
        try:
            url = f"{TELEGRAM_API_URL}/getUpdates"
            if offset:
                url += f"?offset={offset}"

            response = requests.get(url)
            data = response.json()

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                message = update.get("message", {})
                text = message.get("text")
                msg_timestamp = message.get("date") 

                if text:
                    print("📩 Received:", text)

                    # Split input into lines (sentences)
                    lines = text.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue

                        loc_status = extract_location_status(line)
                        if loc_status["location"]:
                            update_firestore_status(loc_status['location'], loc_status['status'], msg_timestamp)
                            time.sleep(2)

                    break  # Process one batch per cycle

        except Exception as e:
            print("⚠️ Polling error:", e)

        time.sleep(10)


# === Start Telegram Bot in Background ===
def start_polling():
    polling_thread = threading.Thread(target=telegram_polling_loop)
    polling_thread.daemon = True
    polling_thread.start()

# === Start Flask and Bot ===
if __name__ == '__main__':
    start_polling()
    print("🚀 Starting Flask server...")
    app.run(debug=True)
