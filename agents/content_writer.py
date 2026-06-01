"""
Content Writer Agent — генерирует статьи для блога и посты для Telegram.

Что делает:
1. Читает MARKETING_PLAN.md и SEO_KEYWORDS.md
2. Генерирует 2 статьи для блога (1500-2000 слов)
3. Адаптирует в посты для Telegram
4. Генерирует описания картинок через Pollinations.ai

Использование:
  python agents/content_writer.py
"""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
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


# ── Генератор картинок через Pollinations.ai ───────────────────────────


def generate_image_description(article_title: str, article_theme: str) -> str:
    """Генерирует описание картинки через DeepSeek и возвращает URL Pollinations.ai."""

    prompt_text = f"""Опиши изображение для статьи на тему "{article_theme}".

Требования к описанию:
- Спокойные пастельные тона (бежевый, мягкий зелёный, приглушённый синий)
- Минималистичный стиль
- Без текста на изображении
- Атмосфера: уютная, безопасная, профессиональная
- Никаких лиц людей (только силуэты или абстракция)

Верни ТОЛЬКО описание на английском языке для генерации картинки, без дополнительного текста."""

    description = ask_deepseek(
        "Ты — AI-арт-директор. Опиши изображение для статьи по психологии.",
        prompt_text,
        max_tokens=200,
    )

    # Формируем URL для Pollinations.ai (бесплатный API, не требует ключа)
    import urllib.parse

    encoded = urllib.parse.quote(description.strip())
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=800&height=400&nologo=true"

    return image_url, description.strip()


# ── Генерация статьи для блога ─────────────────────────────────────────


def generate_blog_article(
    article_number: int,
    article_type: str,
    marketing_plan: str,
    seo_keywords: str,
) -> str:
    """Генерирует одну статью для блога через DeepSeek."""

    system_prompt = """Ты — профессиональный копирайтер и психолог. Пишешь статью для блога психолога Анастасии Палютиной.

Требования к статье:
- Объём: 1500-2000 слов
- Язык: русский
- Тон: профессиональный, тёплый, доверительный, без академизма
- Структура: заголовок → введение → основная часть (2-3 подраздела) → практические советы → CTA
- В конце статьи — призыв записаться на консультацию к Анастасии Палютиной
- Используй ключевые слова естественно, не переспамливай

Формат вывода (Markdown):
# [Заголовок статьи]

[Введение — 2-3 абзаца]

## [Подзаголовок 1]
[Текст]

## [Подзаголовок 2]
[Текст]

## [Подзаголовок 3]
[Текст]

## Что делать прямо сейчас
[3-5 практических рекомендаций]

---

*Записаться на консультацию: [контакты на сайте](https://dimass936.github.io/Site-phsycho/contact.html)*"""

    user_prompt = f"""Тип статьи: {article_type}

=== МАРКЕТИНГОВЫЙ ПЛАН ===
{marketing_plan[:2000]}

=== КЛЮЧЕВЫЕ СЛОВА ===
{seo_keywords[:1500]}

Напиши статью №{article_number} для блога. Используй ключевые слова из раздела, соответствующего теме статьи.
Статья должна решать конкретную проблему читателя и мягко подводить к записи на консультацию."""

    print(f"  📝 Генерация статьи №{article_number} ({article_type})...")
    article = ask_deepseek(system_prompt, user_prompt, max_tokens=4000)
    return article


# ── Адаптация статьи в Telegram-пост ────────────────────────────────────


def adapt_for_telegram(article: str) -> str:
    """Создаёт короткий пост для Telegram на основе статьи."""

    system_prompt = """Ты — SMM-менеджер. Адаптируй статью в пост для Telegram-канала психолога.

Требования к посту:
- Длина: 500-1000 знаков (не слов!)
- Сохрани основную мысль статьи
- Добавь эмодзи (умеренно)
- Закончи вопросом к аудитории для вовлечения
- Добавь ссылку на полную статью на сайте
- Тон: тёплый, как дружеский совет

Верни ТОЛЬКО текст поста, без заголовков и мета-информации."""

    post = ask_deepseek(
        system_prompt,
        f"Статья:\n\n{article[:3000]}",
        max_tokens=800,
    )
    return post


# ── Главный процесс ─────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("📝 Content Writer Agent — запуск")
    print("=" * 60)

    # Читаем исходные данные
    marketing_plan = read_file("MARKETING_PLAN.md")
    seo_keywords = read_file("SEO_KEYWORDS.md")

    if "[Файл MARKETING_PLAN.md не найден]" in marketing_plan:
        print(
            "❌ MARKETING_PLAN.md не найден. Сначала запустите CMO Agent: python agents/cmo_agent.py"
        )
        return

    # Генерируем статьи
    articles = [
        {
            "num": 1,
            "type": "Проблема и решение — статья, которая описывает конкретную психологическую проблему (тревожность, выгорание или детские трудности) и предлагает путь решения через терапию",
        },
        {
            "num": 2,
            "type": "Практическое руководство — статья с конкретными техниками и упражнениями, которые читатель может применить самостоятельно (например, '5 упражнений для снижения тревоги' или 'Как говорить с ребёнком о сложных эмоциях')",
        },
    ]

    for article in articles:
        print(f"\n📄 Статья {article['num']}/2")
        print(f"   Тема: {article['type'][:60]}...")

        # 1. Генерируем статью
        content = generate_blog_article(
            article["num"], article["type"], marketing_plan, seo_keywords
        )

        # 2. Сохраняем статью
        title = content.split("\n")[0].replace("# ", "").strip()
        meta = f"""---
дата: {datetime.now().strftime("%d.%m.%Y")}
автор: Анастасия Палютина
категория: Психология
ключевые_слова: {", ".join(content.split()[:10])}
---

"""
        article_file = f"blog/article-{article['num']}.md"
        write_file(article_file, meta + content)

        # 3. Генерируем картинку
        print(f"   🎨 Генерация описания картинки...")
        image_url, image_desc = generate_image_description(title, article["type"])

        # 4. Адаптируем для Telegram
        print(f"   ✍️  Адаптация для Telegram...")
        telegram_post = adapt_for_telegram(content)

        # 5. Сохраняем Telegram-пост
        telegram_content = f"""# Пост для Telegram

**Дата:** {datetime.now().strftime("%d.%m.%Y")}

---

{telegram_post}

---

**🔗 Читать полную статью:** [на сайте](https://dimass936.github.io/Site-phsycho/blog.html)

**🖼️ Картинка к посту:**
![Иллюстрация]({image_url})

*Описание картинки: {image_desc}*
"""
        telegram_file = f"telegram/post-{article['num']}.md"
        write_file(telegram_file, telegram_content)

    print("\n" + "=" * 60)
    print("✅ Готово! Созданы файлы:")
    print("   blog/article-1.md  — статья (проблема + решение)")
    print("   blog/article-2.md  — статья (практическое руководство)")
    print("   telegram/post-1.md — пост для Telegram")
    print("   telegram/post-2.md — пост для Telegram")
    print("=" * 60)


if __name__ == "__main__":
    main()
