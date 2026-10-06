import os
from openai import OpenAI

API_KEY = ""

# Change these depending on the provider
# BASE_URL = "https://api.openai.com/v1"
# MODEL = "gpt-5-mini"

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODEL = "gemini-3.8-flash"

# BASE_URL = "https://api.groq.com/openai/v1"
# MODEL = "llama-3.3-70b-versatile"

# BASE_URL = "https://openrouter.ai/api/v1"
# MODEL = "google/gemini-2.5-flash"
try:
    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "Reply with exactly: API key works"}
        ],
        max_tokens=20
    )

    print("\n✅ API KEY WORKS")
    print("Provider endpoint:", BASE_URL)
    print("Model:", MODEL)
    print("Response:", response.choices[0].message.content)

except Exception as e:
    print("\n❌ API KEY FAILED")
    print(type(e).__name__ + ":", e)