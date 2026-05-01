from groq import Groq
from config import Config
from prompt import build_system_prompt, build_user_prompt

client = Groq(api_key=Config.GROQ_API_KEY)

def generate(idea: str):
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(idea)

    response = client.chat.completions.create(
        model=Config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content