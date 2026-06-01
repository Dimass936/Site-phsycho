"""Анализирует стиль постов из style_examples.json через DeepSeek."""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

style_file = os.path.join(PROJECT_DIR, "style_examples.json")
if not os.path.exists(style_file):
    sys.exit(1)

with open(style_file) as f:
    examples = json.load(f)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
)

texts = "\n---\n".join([e["text"][:500] for e in examples])

r = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "system",
            "content": "Ты аналитик стиля. Проанализируй посты и напиши гайд: тон, длина, эмодзи, структура, обращения, характерные фразы. 5-7 пунктов. На русском.",
        },
        {"role": "user", "content": texts},
    ],
    temperature=0.5,
    max_tokens=1000,
)

guide = r.choices[0].message.content or "Не удалось проанализировать"

with open(os.path.join(PROJECT_DIR, "STYLE_GUIDE.md"), "w") as f:
    f.write(guide)

# Сохраняем в Obsidian
vault = "/Users/dmitrii/ИИ/2й Поток/Brain/wiki/marketing"
os.makedirs(vault, exist_ok=True)
with open(os.path.join(vault, "style-guide.md"), "w") as f:
    f.write(f"# Гайд по стилю\n\n{guide}")

print(f"OK: {len(examples)} постов проанализировано")
print(guide[:500])
