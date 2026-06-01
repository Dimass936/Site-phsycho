"""
Weekly Reporter — анализирует недельную работу команды.

Что делает:
1. Собирает все файлы, созданные за неделю
2. Считает статистику: сколько статей, постов
3. Через DeepSeek анализирует качество контента
4. Создаёт reports/weekly-YYYY-MM-DD.md
5. Отправляет краткую версию в Telegram

Запуск:
  python agents/weekly_reporter.py              # ручной запуск
  python agents/weekly_reporter.py --notify      # + уведомление в Telegram
"""

import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_ID = os.getenv("TELEGRAM_USER_ID")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if not API_KEY:
    print("❌ DEEPSEEK_API_KEY не задан")
    sys.exit(1)

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")


# ── Утилиты ────────────────────────────────────────────────────────────


def read_file(path: str) -> str:
    full_path = os.path.join(PROJECT_DIR, path)
    if not os.path.exists(full_path):
        return ""
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str):
    full_path = os.path.join(PROJECT_DIR, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)


def ask_deepseek(system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=4000,
    )
    return response.choices[0].message.content


def send_telegram(text: str):
    """Отправляет сообщение владельцу бота."""
    if not BOT_TOKEN or not USER_ID:
        print("⚠️  Telegram не настроен — пропускаем уведомление")
        return

    import requests

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": USER_ID, "text": text[:4096], "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            print("✅ Уведомление отправлено в Telegram")
        else:
            print(f"⚠️  Telegram ошибка: {r.status_code}")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")


# ── Сбор статистики ────────────────────────────────────────────────────


def collect_weekly_stats() -> dict:
    """Собирает статистику по файлам за последние 7 дней."""
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    monday = now - timedelta(days=now.weekday())

    stats = {
        "articles": 0,
        "article_files": [],
        "telegram_posts": 0,
        "telegram_files": [],
        "calendar_files": [],
        "report_files": [],
        "total_files": 0,
        "all_content": "",
    }

    tracked_dirs = ["blog", "telegram"]
    tracked_prefixes = ["MARKETING_PLAN.md", "TELEGRAM_CONTENT_CALENDAR.md"]

    # Считаем файлы в blog/ и telegram/
    for d in tracked_dirs:
        dir_path = os.path.join(PROJECT_DIR, d)
        if not os.path.exists(dir_path):
            continue

        for fn in os.listdir(dir_path):
            full = os.path.join(dir_path, fn)
            mtime = datetime.fromtimestamp(os.path.getmtime(full))

            if mtime < week_ago:
                continue

            rel = os.path.join(d, fn)
            if d == "blog":
                stats["articles"] += 1
                stats["article_files"].append(rel)
                stats["all_content"] += read_file(rel)[:2000] + "\n---\n"
            elif d == "telegram":
                stats["telegram_posts"] += 1
                stats["telegram_files"].append(rel)
                stats["all_content"] += read_file(rel)[:1500] + "\n---\n"

            stats["total_files"] += 1

    # MARKETING_PLAN и CALENDAR
    for fname in tracked_prefixes:
        full = os.path.join(PROJECT_DIR, fname)
        if os.path.exists(full):
            mtime = datetime.fromtimestamp(os.path.getmtime(full))
            if mtime >= week_ago:
                stats["calendar_files"].append(fname)

    # Отчёты
    reports_dir = os.path.join(PROJECT_DIR, "reports")
    if os.path.exists(reports_dir):
        for fn in os.listdir(reports_dir):
            full = os.path.join(reports_dir, fn)
            mtime = datetime.fromtimestamp(os.path.getmtime(full))
            if mtime >= week_ago:
                stats["report_files"].append(f"reports/{fn}")

    return stats


def analyze_with_deepseek(stats: dict) -> str:
    """Анализирует контент через DeepSeek и возвращает рекомендации."""

    system_prompt = """Ты — маркетинговый аналитик. Проанализируй недельный контент психолога Анастасии Палютиной.

На основе предоставленного контента напиши:
1. Лучшие темы — что сработало хорошо и почему (2-3 предложения)
2. Слабые темы — что можно улучшить и как (2-3 предложения)
3. Рекомендации на следующую неделю — конкретные темы и форматы (3-5 пунктов)

Будь конкретным. Пиши на русском. Не更长 800 знаков."""

    user_prompt = f"Контент за неделю:\n\n{stats['all_content'][:6000]}"

    print("🧠 Анализ через DeepSeek...")
    analysis = ask_deepseek(system_prompt, user_prompt)
    return analysis


def generate_report(stats: dict, analysis: str) -> str:
    """Формирует полный отчёт в Markdown."""

    now = datetime.now()
    monday = now - timedelta(days=now.weekday())
    sunday = monday + timedelta(days=6)

    report = f"""# Недельный отчёт

> Период: {monday.strftime("%d.%m.%Y")} — {sunday.strftime("%d.%m.%Y")}
> Сгенерирован: {now.strftime("%d.%m.%Y %H:%M")}
> Модель: {MODEL}

---

## 📊 Создано

- Статей: {stats["articles"]}
- Постов в Telegram: {stats["telegram_posts"]}
- Всего файлов: {stats["total_files"]}

### Статьи
{chr(10).join(f"- {f}" for f in stats["article_files"]) or "- Нет"}

### Посты
{chr(10).join(f"- {f}" for f in stats["telegram_files"]) or "- Нет"}

### Планы и календари
{chr(10).join(f"- {f}" for f in stats["calendar_files"]) or "- Нет"}

---

## 🔍 Анализ (DeepSeek)

{analysis}

---

## 📈 Метрики

| Метрика | Значение |
|---------|----------|
| Новые подписчики | _ожидает данных_ |
| Просмотры | _ожидает данных_ |
| Статьи | {stats["articles"]} |
| Посты | {stats["telegram_posts"]} |

---

## 📋 Действия на следующую неделю

1. Учесть рекомендации из анализа выше
2. Запустить orchestrator.py для генерации нового контента
3. Проверить отправку постов в Telegram-канал
"""
    return report


def generate_summary(stats: dict, analysis: str) -> str:
    """Создаёт краткую версию для Telegram."""
    return f"""📊 <b>Недельный отчёт</b>

Создано: {stats["articles"]} статей, {stats["telegram_posts"]} постов

<b>Анализ:</b>
{analysis[:500]}

📁 Полный отчёт: reports/weekly-{datetime.now().strftime("%Y-%m-%d")}.md"""


# ── Главный процесс ─────────────────────────────────────────────────────


def main():
    notify = "--notify" in sys.argv

    print("=" * 50)
    print("📊 Weekly Reporter — запуск")
    print("=" * 50)

    # 1. Собираем статистику
    print("📁 Сбор статистики...")
    stats = collect_weekly_stats()
    print(f"   Статьи: {stats['articles']}")
    print(f"   Посты: {stats['telegram_posts']}")
    print(f"   Всего: {stats['total_files']}")

    # 2. Анализируем через DeepSeek
    analysis = analyze_with_deepseek(stats)

    # 3. Формируем отчёт
    report = generate_report(stats, analysis)

    # 4. Сохраняем
    report_path = f"reports/weekly-{datetime.now().strftime('%Y-%m-%d')}.md"
    write_file(report_path, report)
    print(f"✅ Отчёт сохранён: {report_path}")

    # 5. Отправляем в Telegram
    if notify:
        print("📤 Отправка в Telegram...")
        summary = generate_summary(stats, analysis)
        send_telegram(summary)

    print("=" * 50)
    print("✅ Weekly Reporter завершил работу")
    print("=" * 50)


if __name__ == "__main__":
    main()
