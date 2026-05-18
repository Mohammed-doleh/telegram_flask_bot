# 🤖 Telegram Road Status Bot

A Python Flask bot that listens to Arabic Telegram messages, extracts location and road status using an AI model (Hugging Face), and updates a Firebase Firestore database in real time.

---

## 📋 Overview

This project automates the process of updating road/checkpoint statuses from a Telegram group or channel. When a message like **"عزون مسكرة"** is sent, the bot:

1. Receives the message via Telegram polling
2. Sends it to a Hugging Face AI model to extract the **location name** and **status**
3. Updates the matching document in **Firebase Firestore**

---

## 🗂️ Project Structure

```
telegram_flask_bot/
├── app.py                  # Main Flask app + Telegram polling logic
├── .env                    # Environment variables (never commit this)
├── firebase-adminsdk.json  # Firebase credentials (never commit this)
├── .gitignore
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/Mohammed-doleh/telegram_flask_bot.git
cd telegram_flask_bot
```

### 2. Install dependencies
```bash
pip install flask requests firebase-admin python-dotenv
```

### 3. Create your `.env` file
```env
BOT_TOKEN=your_telegram_bot_token
HF_API_KEY=your_huggingface_api_key
HF_MODEL=your_huggingface_model_name
```

### 4. Add Firebase credentials
Place your `firebase-adminsdk.json` file in the project root (download it from Firebase Console → Project Settings → Service Accounts).

### 5. Run the app
```bash
python app.py
```

---

## 🔧 How It Works

```
Telegram Message
      ↓
Flask App (polling)
      ↓
Hugging Face AI → extracts "location - status"
      ↓
Firebase Firestore → updates 'Gate' collection
```

### Status Mapping (Arabic)
| Input keyword | Stored Status |
|---|---|
| مفتوح / سالكة | مفتوح (Open) |
| مسكر / مسكرة | مغلق (Closed) |
| أزمة / أزمة خانقة | أزمة (Traffic jam) |

---

## 🔒 Security

- **Never commit** `.env` or `firebase-adminsdk.json` to GitHub
- Both files are listed in `.gitignore`
- All API keys and credentials must be stored as environment variables only

---

## 🛠️ Technologies Used

- [Python](https://python.org) + [Flask](https://flask.palletsprojects.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Hugging Face Inference API](https://huggingface.co/inference-api)
- [Firebase Firestore](https://firebase.google.com/docs/firestore)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

---

## 🔗 Related Projects

- **Flutter Mobile App** → [roads](https://github.com/Mohammed-doleh/roads)
  The Flutter app that displays the checkpoint statuses updated by this bot.

---

## 📄 License

MIT License — feel free to use and modify.
