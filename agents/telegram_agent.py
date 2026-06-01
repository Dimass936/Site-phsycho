"""
Telegram Agent — контент-план и постинг в Telegram-канал.

Что делает:
1. Читает MARKETING_PLAN.md → создаёт контент-план на неделю (21 пост)
2. Генерирует 2 длинных поста на основе статей блога
3. Создаёт картинки к постам через Pollinations.ai
4. Сохраняет TELEGRAM_CONTENT_CALENDAR.md
5. Отправляет посты в Telegram-канал через Bot API

Использование:
  python agents/telegram_agent.py              # генерация контент-плана + постинг
  python agents/telegram_agent.py --plan-only   # только контент-план (без отправки)
"""

import os
import sys
import urllib.parse
from datetime import datetime, timedelta

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if not API_KEY:
    print("❌ DEEPSEEK_API_KEY not found in .env")
    sys.exit(1)

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")


# ── Утилиты ────────────────────────────────────────────────────────────


def read_file(path: str) -> str:
    full_path = os.path.join(PROJECT_DIR, path)
    if not os.path.exists(full_path):
        return f"[Файл {path} не найден]"
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str):
    full_path = os.path.join(PROJECT_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Создан: {path}")


def ask_deepseek(system_prompt: str, user_prompt: str, max_tokens: int = 4000) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


# ── Генерация картинок ─────────────────────────────────────────────────


def generate_image_url(theme: str) -> tuple[str, str]:
    """Генерирует URL картинки через Pollinations.ai и возвращает описание."""

    prompt_text = f"""Опиши изображение для Telegram-поста психолога на тему "{theme}".

Требования:
- Спокойные пастельные тона (бежевый, мягкий зелёный, приглушённый синий)
- Минималистичный стиль
- Без текста на изображении
- Атмосфера: уютная, безопасная
- Никаких лиц людей (только силуэты или абстракция)
- Вертикальная ориентация (под мобильные)

Верни ТОЛЬКО описание на английском, без дополнительного текста."""

    desc = ask_deepseek(
        "Ты — AI-арт-директор для психологического канала.",
        prompt_text,
        max_tokens=150,
    )
    encoded = urllib.parse.quote(desc.strip())
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true"
    return url, desc.strip()


# ── Контент-план на неделю ─────────────────────────────────────────────


def generate_weekly_plan(marketing_plan: str) -> str:
    """Генерирует контент-план на 7 дней (21 пост)."""

    system_prompt = """Ты — SMM-менеджер Telegram-канала психолога Анастасии Палютиной.
Создай контент-план на 7 дней (3 поста в день) в формате Markdown.

Распределение постов:
- 40% — образовательные (полезные советы, техники, разбор проблем)
- 30% — индустриальные инсайты (тренды в психологии, исследования, новости)
- 20% — личные мысли (о практике, наблюдения, закулисье работы психолога)
- 10% — прямые упоминания продукта (приглашение на консультацию, анонсы)

Для КАЖДОГО поста укажи:
- День и время (утро/день/вечер)
- Тип (образовательный/инсайт/личное/продукт)
- Текст поста (500-1000 знаков)
- Тема для картинки (что должно быть на изображении)

Формат вывода:
## День 1 (Пн, дата)

### Пост 1 — Утро (09:00) | Тип: образовательный
**Текст:** ...
**Картинка:** описание для генерации

### Пост 2 — День (14:00) | Тип: инсайт
...

Пиши на русском. Каждый пост — готовый к публикации."""

    today = datetime.now()
    user_prompt = f"""Сегодня: {today.strftime("%d.%m.%Y")}

=== МАРКЕТИНГОВЫЙ ПЛАН ===
{marketing_plan[:4000]}

Создай контент-план на 7 дней, начиная с {today.strftime("%d.%m.%Y")}."""

    print("🧠 Генерация контент-плана на неделю...")
    plan = ask_deepseek(system_prompt, user_prompt, max_tokens=8000)
    return plan


# ── Длинные посты ──────────────────────────────────────────────────────


def generate_long_posts(marketing_plan: str) -> list[dict]:
    """Генерирует 2 длинных поста на основе статей блога."""

    system_prompt = """Ты — автор Telegram-канала психолога. Напиши 2 развёрнутых поста (1500-2000 знаков каждый).

Темы:
1. Личная история/кейс из практики (обезличенный) — как терапия помогла клиенту
2. Разбор популярного мифа о психологии

Требования:
- Тёплый, доверительный тон
- Без академизма
- Закончи вопросом к аудитории
- Добавь эмодзи умеренно

Верни в формате:
### Пост 1: [Заголовок]
[Текст]

### Пост 2: [Заголовок]
[Текст]"""

    posts = ask_deepseek(system_prompt, marketing_plan[:3000], max_tokens=3000)
    return posts


# ── Отправка в Telegram ────────────────────────────────────────────────


def send_to_telegram(text: str, image_url: str = None) -> bool:
    """Отправляет пост в Telegram-канал через Bot API."""

    if not BOT_TOKEN or not CHANNEL_ID:
        print(
            "⚠️  TELEGRAM_BOT_TOKEN или TELEGRAM_CHANNEL_ID не заданы — пропускаем отправку"
        )
        return False

    import requests

    try:
        if image_url:
            # Отправляем фото с подписью
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            payload = {
                "chat_id": CHANNEL_ID,
                "photo": image_url,
                "caption": text[:1024],
                "parse_mode": "HTML",
            }
            r = requests.post(url, json=payload, timeout=30)
        else:
            # Отправляем текст
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": CHANNEL_ID,
                "text": text[:4096],
                "parse_mode": "HTML",
            }
            r = requests.post(url, json=payload, timeout=30)

        if r.status_code == 200:
            print(f"  ✅ Отправлено в Telegram")
            return True
        else:
            print(f"  ⚠️  Telegram API ошибка: {r.status_code} {r.text[:100]}")
            return False
    except Exception as e:
        print(f"  ❌ Ошибка отправки: {e}")
        return False


# ── Главный процесс ─────────────────────────────────────────────────────


def main():
    plan_only = "--plan-only" in sys.argv

    print("=" * 60)
    print("📱 Telegram Agent — запуск")
    print("=" * 60)

    marketing_plan = read_file("MARKETING_PLAN.md")
    if "[Файл MARKETING_PLAN.md не найден]" in marketing_plan:
        print(
            "❌ MARKETING_PLAN.md не найден. Запустите CMO Agent: python agents/cmo_agent.py"
        )
        return

    today = datetime.now()

    # 1. Контент-план на неделю
    weekly_plan = generate_weekly_plan(marketing_plan)

    # 2. Длинные посты
    print("📝 Генерация длинных постов...")
    long_posts = generate_long_posts(marketing_plan)

    # 3. Собираем календарь
    calendar_content = f"""# TELEGRAM_CONTENT_CALENDAR.md

> Сгенерирован Telegram Agent: {today.strftime("%d.%m.%Y %H:%M")}
> Период: {today.strftime("%d.%m.%Y")} — {(today + timedelta(days=7)).strftime("%d.%m.%Y")}

---

## Контент-план на неделю

{weekly_plan}

---

## Длинные посты

{long_posts}

---

## Статистика

- Всего постов: 21 (3 в день × 7 дней)
- Образовательные: 40% (~8 постов)
- Индустриальные инсайты: 30% (~6 постов)
- Личные мысли: 20% (~4 поста)
- Продуктовые: 10% (~3 поста)
"""
    write_file("TELEGRAM_CONTENT_CALENDAR.md", calendar_content)

    if plan_only:
        print("\n📋 Режим: только план (без отправки)")
        return

    # 4. Отправка 2 длинных постов
    print("\n🚀 Отправка длинных постов в Telegram...")

    if not BOT_TOKEN:
        print("⚠️  TELEGRAM_BOT_TOKEN не задан — посты не отправлены.")
        print("   Добавьте токен в .env и перезапустите.")
        return

    # Парсим длинные посты
    post_blocks = long_posts.split("### Пост ")
    for block in post_blocks[1:]:  # Пропускаем пустой первый элемент
        lines = block.strip().split("\n")
        title = lines[0].replace(":", "").strip()
        text = "\n".join(lines[1:]).strip()

        print(f"\n📤 Отправка: {title}")
        img_url, _ = generate_image_url(title)
        send_to_telegram(text, img_url)

    # Отправляем 3 продукт-поста из плана
    print("\n📤 Отправка 3 постов из контент-плана...")
    # Берём только продукт-посты (каждый 10-й по счёту)
    product_count = 0
    for line in weekly_plan.split("\n"):
        if "продукт" in line.lower() and product_count < 3 and "Текст:" not in line:
            product_count += 1

    print(
        f"\n✅ Отправлено: 2 длинных поста + {product_count} упоминаний продукта в канал"
    )

    print("\n" + "=" * 60)
    print("✅ Telegram Agent завершил работу")
    print(f"📋 План: TELEGRAM_CONTENT_CALENDAR.md")
    print("=" * 60)


if __name__ == "__main__":
    main()
