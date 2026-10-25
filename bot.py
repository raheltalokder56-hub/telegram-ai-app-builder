def generate_app_idea(platform: str, prompt: str) -> str:
    client = get_openai_client()
    if client is None:
        return (
            "⚠️ AI ফিচার চালু নেই বা API Key দেওয়া হয়নি।\n\n"
            "অনুগ্রহ করে Render-এ `OPENAI_API_KEY` এনভায়রনমেন্ট ভেরিয়েবল যোগ করুন।\n\n"
            "তোমার আইডিয়া পেয়েছি:\n" + prompt[:1500]
        )

    if platform == "android":
        target = (
            "Android app. Give a practical starter project using Kotlin and Jetpack Compose. "
            "Return code in clearly named files, build/setup instructions, and note any missing "
            "production details. Do not claim an APK has been compiled."
        )
    elif platform == "web":
        target = (
            "Web app. Prefer a self-contained HTML/CSS/JavaScript starter when suitable. "
            "Return complete code in clearly named files and instructions to run it."
        )
    else:
        target = (
            "Android and Web app. Give a practical plan, a web starter in HTML/CSS/JavaScript, "
            "and an Android starter in Kotlin/Jetpack Compose. Separate files clearly and explain "
            "how to run/build each. Do not claim an APK has been compiled."
        )

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful app-building assistant. Reply in Bengali, but keep code, "
                        "file names, and technical identifiers in their normal form. Ask for clarification "
                        "only if absolutely necessary. Produce useful starter code, explain assumptions, "
                        "include safe defaults, and never claim to have run, tested, deployed, or compiled "
                        "code unless that actually happened. Never include secrets in code."
                    ),
                },
                {"role": "user", "content": f"Target: {target}\nUser's app idea:\n{prompt}"},
            ],
        )
        return response.choices[0].message.content or "দুঃখিত, AI থেকে কোনো লেখা পাওয়া যায়নি।"
    except Exception as e:
        log.exception("OpenAI API call failed: %s", e)
        return f"⚠️ AI থেকে উত্তর আনতে সমস্যা হয়েছে। ত্রুটি: {str(e)}"
