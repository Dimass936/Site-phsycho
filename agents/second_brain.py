"""
Second Brain Agent — связывает ИИ-агентов с Obsidian-хранилищем.

Читает:
  - wiki/marketing/latest-report.md     — последний недельный отчёт
  - wiki/marketing/successful-posts.md  — удачные посты
  - wiki/marketing/failed-posts.md      — провальные посты

Пишет:
  - wiki/marketing/content/             — статьи от content_writer
  - wiki/marketing/tweets/              — твиты/посты
  - wiki/marketing/latest-report.md     — обновления от weekly_reporter

Использование:
  python agents/second_brain.py                           # показать статус
  python agents/second_brain.py --save-content PATH TEXT  # сохранить контент
  python agents/second_brain.py --save-tweet TEXT         # сохранить твит
  python agents/second_brain.py --update-report PATH      # обновить отчёт
  python agents/second_brain.py --context                 # вернуть контекст для промпта
"""

import os
import sys
from datetime import datetime

VAULT = "/Users/dmitrii/ИИ/2й Поток/Brain"
MARKETING = os.path.join(VAULT, "wiki", "marketing")


# ── Чтение из Obsidian ─────────────────────────────────────────────────


def read_vault_file(relative_path: str) -> str:
    """Читает файл из Obsidian-хранилища."""
    full_path = os.path.join(VAULT, relative_path)
    if not os.path.exists(full_path):
        return ""
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()


def write_vault_file(relative_path: str, content: str) -> None:
    """Пишет файл в Obsidian-хранилище."""
    full_path = os.path.join(VAULT, relative_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        _ = f.write(content)
    print(f"✅ Obsidian: {relative_path}")


# ── Основные методы ────────────────────────────────────────────────────


def get_context_for_agents() -> str:
    """Возвращает контекст для агентов: что сработало, что нет, рекомендации."""
    report = read_vault_file("wiki/marketing/latest-report.md")
    successful = read_vault_file("wiki/marketing/successful-posts.md")
    failed = read_vault_file("wiki/marketing/failed-posts.md")

    ctx: list[str] = []
    if report and "Ещё не сгенерирован" not in report:
        ctx.append("## Из последнего отчёта\n" + report[:2000])
    if successful and "Пока пусто" not in successful:
        ctx.append("## Успешные темы (повторить)\n" + successful[:1000])
    if failed and "Пока пусто" not in failed:
        ctx.append("## Провальные темы (избегать)\n" + failed[:1000])

    return (
        "\n\n".join(ctx)
        if ctx
        else "⚠️ Второй мозг пуст — используй стандартную стратегию."
    )


def get_context_prompt() -> str:
    """Возвращает промпт-инструкцию для агентов на основе второго мозга."""
    ctx = get_context_for_agents()

    return f"""=== ИНСТРУКЦИЯ ИЗ ВТОРОГО МОЗГА (Obsidian) ===

{ctx}

На основе этих данных:
- ИЗБЕГАЙ провальных тем и форматов
- РАЗВИВАЙ успешные темы
- УЧИТЫВАЙ рекомендации из отчёта
"""


def show_status() -> str:
    """Показывает статус второго мозга."""
    files: list[tuple[str, int, str]] = []
    for root, _, filenames in os.walk(MARKETING):
        for fn in filenames:
            full = os.path.join(root, fn)
            size = os.path.getsize(full)
            mtime = datetime.fromtimestamp(os.path.getmtime(full)).strftime(
                "%d.%m %H:%M"
            )
            rel = os.path.relpath(full, VAULT)
            files.append((mtime, size, rel))

    files.sort(reverse=True)

    lines = ["📁 Второй мозг (Obsidian):\n"]
    for mtime, size, name in files[:20]:
        lines.append(f"  {mtime}  {size:>6}B  {name}")

    return "\n".join(lines)


def update_successful_posts(title: str, reason: str):
    """Добавляет пост в успешные."""
    current = read_vault_file("wiki/marketing/successful-posts.md")
    entry = (
        f"\n### {title}\n{reason}\n_Добавлено: {datetime.now().strftime('%d.%m.%Y')}_\n"
    )
    write_vault_file("wiki/marketing/successful-posts.md", current + entry)


def update_failed_posts(title: str, reason: str):
    """Добавляет пост в провальные."""
    current = read_vault_file("wiki/marketing/failed-posts.md")
    entry = (
        f"\n### {title}\n{reason}\n_Добавлено: {datetime.now().strftime('%d.%m.%Y')}_\n"
    )
    write_vault_file("wiki/marketing/failed-posts.md", current + entry)


def save_content(article_id: str, content: str) -> None:
    """Сохраняет контент в Obsidian."""
    write_vault_file(f"wiki/marketing/content/article-{article_id}.md", content)
    print("   📝 + теги для Obsidian: #marketing #article")


def update_latest_report(report_content: str):
    """Обновляет последний отчёт."""
    write_vault_file("wiki/marketing/latest-report.md", report_content)


# ── CLI ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--context" in sys.argv:
        print(get_context_prompt())
    elif "--save-content" in sys.argv:
        article_id = sys.argv[sys.argv.index("--save-content") + 1]
        content = sys.stdin.read().strip() or " ".join(
            sys.argv[sys.argv.index("--save-content") + 2 :]
        )
        save_content(article_id, content)
    elif "--save-tweet" in sys.argv:
        tweet = " ".join(sys.argv[sys.argv.index("--save-tweet") + 1 :])
        now = datetime.now().strftime("%Y-%m-%d")
        write_vault_file(f"wiki/marketing/tweets/tweet-{now}.md", tweet)
    elif "--update-report" in sys.argv:
        report_path = sys.argv[sys.argv.index("--update-report") + 1]
        with open(report_path, "r") as f:
            update_latest_report(f.read())
    else:
        print(show_status())
