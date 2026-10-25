# Telegram AI App Builder Bot (বাংলা)

এই প্রজেক্টটি Telegram-এর মধ্যে একটি AI app-builder bot চালায়। এটি Web বা Android starter code এবং নির্দেশনা তৈরি করতে পারে। এটি নিজে APK compile, পরীক্ষা, বা Play Store-এ প্রকাশ করে না।

## যা লাগবে

- Telegram অ্যাকাউন্ট
- Python 3.10 বা তার নতুন সংস্করণ (লোকালে চালালে)
- BotFather থেকে Telegram bot token
- AI provider-এর API key (AI কোড তৈরির জন্য; আলাদা খরচ/সীমা থাকতে পারে)
- GitHub অ্যাকাউন্ট (Render-এ deploy করতে চাইলে)

## ১. Telegram bot token নাও

1. Telegram-এ `@BotFather` খোলো।
2. `/newbot` পাঠাও।
3. বটের নাম ও username সেট করো।
4. BotFather যে token দেবে সেটি গোপন রাখো। কাউকে পাঠিও না এবং GitHub-এ commit করো না।

## ২. Admin Telegram ID বের করো

Telegram-এর কোনো নির্ভরযোগ্য ID bot ব্যবহার করে নিজের numeric user ID দেখো। সেই সংখ্যাটি `ADMIN_IDS` environment variable-এ বসাও। একাধিক admin হলে কমা দিয়ে আলাদা করো, যেমন `123456789,987654321`।

## ৩. AI API key

AI code generation-এর জন্য তোমার নির্বাচিত AI provider-এর API key দরকার। API key-র billing ও usage limit পরীক্ষা করো। API key কখনও বটের chat-এ পাঠিও না।

## ৪. লোকাল কম্পিউটারে চালানো

প্রজেক্ট ফোল্ডারে টার্মিনাল খুলে চালাও:

```bash
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

তারপর:

```bash
pip install -r requirements.txt
```

Environment variables সেট করো।

Windows PowerShell:
```powershell
$env:TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_TOKEN"
$env:OPENAI_API_KEY="YOUR_AI_API_KEY"
$env:OPENAI_MODEL="gpt-6-astra"
$env:ADMIN_IDS="YOUR_NUMERIC_TELEGRAM_ID"
python bot.py
```

macOS/Linux:
```bash
export TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_TOKEN"
export OPENAI_API_KEY="YOUR_AI_API_KEY"
export OPENAI_MODEL="gpt-6-astra"
export ADMIN_IDS="YOUR_NUMERIC_TELEGRAM_ID"
python bot.py
```

Telegram-এ নিজের bot খোলো এবং `/start` পাঠাও।

## ৫. Render-এ ফ্রি-টিয়ার deploy

1. এই প্রজেক্টের ফাইলগুলো নিজের GitHub repository-তে রাখো।
2. `.env` বা আসল token/key কখনও GitHub-এ আপলোড কোরো না।
3. Render-এ sign in করে New → Web Service নির্বাচন করো এবং repository connect করো।
4. Build command: `pip install -r requirements.txt`
5. Start command: `python bot.py`
6. Plan হিসেবে Free নির্বাচন করো (যদি তোমার অ্যাকাউন্টে উপলভ্য থাকে)।
7. Environment Variables-এ `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `ADMIN_IDS` যোগ করো।
8. Deploy করো এবং logs-এ `Telegram bot started` দেখো।
9. `https://তোমার-service.onrender.com/health` খুলে health check যাচাই করো।

**গুরুত্বপূর্ণ সীমাবদ্ধতা:** Render-এর free web service ১৫ মিনিট inbound traffic না পেলে sleep করতে পারে, এবং পরের request-এ জেগে উঠতে সময় লাগে। Free service-এর local filesystem স্থায়ী নয়; তাই SQLite-এ থাকা user stats restart/redeploy-এ হারাতে পারে। নির্ভরযোগ্য স্থায়ী ডেটার জন্য managed database ব্যবহার করো। Polling bot সব সময় অনলাইনে থাকবে—এমন নিশ্চয়তা free hosting-এ নেই।

## ৬. বট ব্যবহার

- `/start` — মেনু
- `/help` — সাহায্য
- `/admin` — শুধু `ADMIN_IDS`-এ থাকা admin ব্যবহার করতে পারবে
- মেনু থেকে Web, Android বা দুটোই নির্বাচন করে অ্যাপের বর্ণনা পাঠাও

## নিরাপত্তা ও বাস্তব সীমা

- এই starter project code/text output দেয়; generated code চালায় না।
- Android APK বানাতে Android build environment/CI pipeline এবং dependencies লাগবে।
- Generated code review ও test না করে production-এ ব্যবহার কোরো না।
- Public bot-এ rate limiting, per-user quotas, abuse controls, persistent database ও error monitoring যোগ করা উচিত।
- API usage-এর খরচ এড়াতে provider dashboard-এ limits সেট করো।
