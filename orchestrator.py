#!/usr/bin/env python3
"""
Orchestrator — запускает всех ИИ-агентов по порядку.

Порядок выполнения:
1. cmo_agent.py      → MARKETING_PLAN.md
2. content_writer.py → blog/article-*.md + telegram/post-*.md
3. telegram_agent.py → TELEGRAM_CONTENT_CALENDAR.md + постинг

Использование:
  python orchestrator.py                 # полный цикл
  python orchestrator.py --no-telegram   # без отправки в Telegram
"""

import os
import subprocess
import sys
from datetime import datetime

AGENTS_DIR = "agents"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Цветной вывод ───────────────────────────────────────────────────────

GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def step(name: str):
    print(f"\n{GREEN}{'=' * 60}{RESET}")
    print(f"{BOLD}{GREEN}▶ {name}{RESET}")
    print(f"{GREEN}{'=' * 60}{RESET}")


def ok(msg: str = ""):
    print(f"{GREEN}✅ {msg}{RESET}")


def warn(msg: str):
    print(f"{YELLOW}⚠️  {msg}{RESET}")


def fail(msg: str):
    print(f"{RED}❌ {msg}{RESET}")


def run_agent(script: str, args: list[str] | None = None) -> bool:
    """Запускает Python-скрипт агента и возвращает True если успешно."""
    script_path = os.path.join(PROJECT_DIR, AGENTS_DIR, script)

    if not os.path.exists(script_path):
        warn(f"Агент не найден: {script_path}")
        return False

    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    print(f"   Запуск: {CYAN}{script}{RESET} {' '.join(args or [])}")

    result = subprocess.run(
        cmd,
        cwd=PROJECT_DIR,
        capture_output=False,  # Показываем вывод в реальном времени
        text=True,
    )

    if result.returncode == 0:
        return True
    else:
        fail(f"Агент {script} завершился с ошибкой (код {result.returncode})")
        return False


# ── Главный процесс ─────────────────────────────────────────────────────


def main():
    no_telegram = "--no-telegram" in sys.argv

    print(
        f"\n{BOLD}{GREEN}╔══════════════════════════════════════════════════════╗{RESET}"
    )
    print(
        f"{BOLD}{GREEN}║        🚀 Orchestrator — запуск всех агентов        ║{RESET}"
    )
    print(
        f"{BOLD}{GREEN}║        {datetime.now().strftime('%d.%m.%Y %H:%M'):<44s}║{RESET}"
    )
    print(
        f"{BOLD}{GREEN}╚══════════════════════════════════════════════════════╝{RESET}"
    )

    results: dict[str, bool] = {}

    # ── Шаг 1: CMO Agent ──
    step("CMO Agent: создаю маркетинговую стратегию...")
    if run_agent("cmo_agent.py"):
        ok("MARKETING_PLAN.md создан")
        results["cmo"] = True
    else:
        fail("CMO Agent не смог создать стратегию")
        results["cmo"] = False

    # ── Шаг 2: Content Writer ──
    step("Content Writer: пишу статьи и адаптирую для Telegram...")
    if run_agent("content_writer.py"):
        ok("blog/article-1.md + article-2.md + telegram/post-1.md + post-2.md")
        results["writer"] = True
    else:
        warn("Content Writer отработал с ошибками — проверьте вывод")
        results["writer"] = False

    # ── Шаг 3: Telegram Agent ──
    step("Telegram Agent: создаю контент-план и отправляю посты...")

    telegram_args = ["--plan-only"] if no_telegram else []
    if run_agent("telegram_agent.py", telegram_args):
        ok("TELEGRAM_CONTENT_CALENDAR.md создан")
        results["telegram"] = True
    else:
        warn("Telegram Agent отработал с ошибками")
        results["telegram"] = False

    # ── Итоги ──
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}📊 Результаты запуска:{RESET}")

    total = len(results)
    success = sum(1 for v in results.values() if v)
    failures = total - success

    if failures == 0:
        print(
            f"\n{GREEN}{BOLD}✅ Готово! Все {total} агента отработали успешно.{RESET}"
        )
    else:
        print(
            f"\n{YELLOW}{BOLD}⚠️  Завершено: {success}/{total} агентов успешно, {failures} с ошибками.{RESET}"
        )

    print(f"\n{BOLD}📁 Созданные файлы:{RESET}")
    files = [
        "MARKETING_PLAN.md",
        "blog/article-1.md",
        "blog/article-2.md",
        "telegram/post-1.md",
        "telegram/post-2.md",
        "TELEGRAM_CONTENT_CALENDAR.md",
    ]
    for f in files:
        path = os.path.join(PROJECT_DIR, f)
        if os.path.exists(path):
            print(f"   ✅ {f}")
        else:
            print(f"   ❌ {f} — не создан")

    if no_telegram:
        print(
            f"\n{YELLOW}📋 Посты НЕ отправлены в Telegram (режим --no-telegram){RESET}"
        )
        print("   Для отправки запустите: python agents/telegram_agent.py")
    else:
        print(f"\n{GREEN}📱 Посты отправлены в Telegram-канал{RESET}")


if __name__ == "__main__":
    main()
