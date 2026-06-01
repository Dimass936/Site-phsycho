"""
CMO Agent — Chief Marketing Officer для сайта психолога Анастасии Палютиной.

Что делает:
1. Читает PRODUCT_STRATEGY.md → создаёт маркетинговую стратегию на месяц через DeepSeek API
2. Распределяет задачи между агентами: SEO, Content Writer, Telegram Agent
3. Создаёт MARKETING_PLAN.md с конкретными задачами и KPI
4. Раз в неделю анализирует результаты и обновляет план

Использование:
  python agents/cmo_agent.py              # генерация стратегии на месяц
  python agents/cmo_agent.py --weekly     # еженедельный анализ
"""

import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
from openai import OpenAI

# ── Загрузка конфигурации ──────────────────────────────────────────────

load_dotenv()

API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if not API_KEY:
    print("❌ DEEPSEEK_API_KEY not found in .env")
    sys.exit(1)

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")


# ── Чтение файлов ──────────────────────────────────────────────────────


def read_file(path: str) -> str:
    full_path = os.path.join(PROJECT_DIR, path)
    if not os.path.exists(full_path):
        return f"[Файл {path} не найден]"
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str):
    full_path = os.path.join(PROJECT_DIR, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Создан: {path}")


# ── DeepSeek API вызов ─────────────────────────────────────────────────


def ask_deepseek(system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=8000,
    )
    result = response.choices[0].message.content
    return result if result is not None else ""


# ── Генерация стратегии на месяц ───────────────────────────────────────


def generate_monthly_strategy():
    print("📊 Чтение стратегии продукта...")
    _ = read_file("PRODUCT_STRATEGY.md")  # загружаем, но используем ниже
    product_strategy = read_file("PRODUCT_STRATEGY.md")
    requirements = read_file("REQUIREMENTS.md")
    project = read_file("PROJECT.md")

    today = datetime.now()
    next_month = today + timedelta(days=30)

    system_prompt = """Ты — Chief Marketing Officer сайта психолога Анастасии Палютиной.
Твоя задача — создать детальный маркетинговый план на месяц.

Контекст о продукте:
- Онлайн-консультации психолога для взрослых, пар, подростков
- Специализации: детская психология, отношения, стресс, тревожность, личностный рост
- Целевая аудитория: родители (28-45 лет), взрослые с тревогой (25-50 лет), пары (25-45 лет)
- Каналы: сайт с блогом, Telegram, Instagram, VK

Создай план в формате Markdown. Строго следуй структуре:

1. Цели на месяц (конкретные цифры)
2. Контент-план на 4 недели (темы статей + темы постов)
3. Задачи для SEO-агента (ключевые слова, оптимизация)
4. Задачи для Content Writer (статьи в блог)
5. Задачи для Telegram Agent (посты, рубрики)
6. KPI для каждого агента
7. График публикаций по дням

План должен быть конкретным: с датами, темами, ключевыми словами.
Используй информацию из PRODUCT_STRATEGY.md для тем и growth loops.
Пиши на русском языке."""

    user_prompt = f"""Сегодня: {today.strftime("%d.%m.%Y")}
Месяц: {today.strftime("%B %Y")} — {next_month.strftime("%B %Y")}

=== СТРАТЕГИЯ ПРОДУКТА ===
{product_strategy[:3000]}

=== ТРЕБОВАНИЯ ===
{requirements[:2000]}

=== ПРОЕКТ ===
{project[:1500]}

Создай маркетинговый план на месяц."""

    print("🧠 Генерация стратегии через DeepSeek...")
    plan_content = ask_deepseek(system_prompt, user_prompt)

    # Добавляем мета-информацию
    header = f"""# MARKETING_PLAN.md — Маркетинговый план

> Сгенерирован CMO Agent: {today.strftime("%d.%m.%Y %H:%M")}
> Период: {today.strftime("%d.%m.%Y")} — {next_month.strftime("%d.%m.%Y")}
> Модель: {MODEL}
> Статус: ✅ Активен

---

"""
    write_file("MARKETING_PLAN.md", header + plan_content)
    print(f"📅 План создан: MARKETING_PLAN.md")
    print(
        f"   Период: {today.strftime('%d.%m.%Y')} — {next_month.strftime('%d.%m.%Y')}"
    )


# ── Еженедельный анализ ────────────────────────────────────────────────


def weekly_analysis():
    print("📈 Запуск еженедельного анализа...")

    marketing_plan = read_file("MARKETING_PLAN.md")
    if "[Файл MARKETING_PLAN.md не найден]" in marketing_plan:
        print(
            "❌ MARKETING_PLAN.md не найден. Сначала создайте план: python agents/cmo_agent.py"
        )
        return

    today = datetime.now()

    system_prompt = """Ты — Chief Marketing Officer. Проанализируй текущий маркетинговый план
и напиши краткий отчёт за неделю в формате Markdown. Разделы:

1. Что должно было быть сделано на этой неделе (из плана)
2. Что рекомендуется скорректировать
3. Приоритеты на следующую неделю
4. Метрики для отслеживания

Будь конкретным. Пиши на русском языке."""

    user_prompt = f"""Сегодня: {today.strftime("%d.%m.%Y")}
Неделя: {today.strftime("%d.%m.%Y")} — это анализная точка.

=== ТЕКУЩИЙ ПЛАН ===
{marketing_plan[:5000]}

Проанализируй и дай рекомендации на следующую неделю."""

    analysis = ask_deepseek(system_prompt, user_prompt)

    report_name = f"WEEKLY_REPORT_{today.strftime('%Y%m%d')}.md"
    header = f"""# Недельный отчёт CMO Agent

> Дата: {today.strftime("%d.%m.%Y")}
> Модель: {MODEL}

---

"""
    write_file(report_name, header + analysis)
    print(f"📊 Отчёт создан: {report_name}")


# ── Точка входа ────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--weekly" in sys.argv:
        weekly_analysis()
    else:
        generate_monthly_strategy()
