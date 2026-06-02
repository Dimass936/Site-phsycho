"""
Telegram Bot — связывает пользователя с маркетинговой командой.

Принимает команды ТОЛЬКО от владельца (TELEGRAM_USER_ID).
Остальным отвечает «Access denied».

Команды:
  /status     — статус команды
  /content    — последние статьи и посты
  /run        — запуск orchestrator.py
  /post       — немедленная публикация текста
  /post_now   — экстренная публикация (текст + картинка)
  /report     — недельный отчёт
  /report_now — принудительный отчёт

Запуск:
  python agents/telegram_bot.py
"""

import os
import subprocess
import sys
from datetime import datetime, time, timedelta

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USER_IDS_RAW = os.getenv("TELEGRAM_USER_ID", "0")
ADMIN_IDS: list[int] = [int(x.strip()) for x in USER_IDS_RAW.split(",") if x.strip()]
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATE_FILE = os.path.join(PROJECT_DIR, "last_post.txt")
PENDING_FILE = os.path.join(PROJECT_DIR, "pending_posts.json")

if not TOKEN or not USER_IDS_RAW:
    print("❌ TELEGRAM_BOT_TOKEN или TELEGRAM_USER_ID не заданы в .env")
    sys.exit(1)


# ── Rate limiter: не чаще раза в неделю ──────────────────────────────


def can_post() -> tuple[bool, str]:
    """Проверяет, можно ли постить. Возвращает (можно, сообщение)."""
    if not os.path.exists(RATE_FILE):
        return True, ""
    with open(RATE_FILE) as f:
        last = f.read().strip()
    last_date = datetime.strptime(last, "%Y-%m-%d")
    next_date = last_date + timedelta(days=7)
    if datetime.now() < next_date:
        return False, next_date.strftime("%d.%m.%Y")
    return True, ""


def mark_posted():
    """Записывает дату последнего поста."""
    with open(RATE_FILE, "w") as f:
        f.write(datetime.now().strftime("%Y-%m-%d"))


# ── Импорты телеграм ────────────────────────────────────────────────
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update

# ── Проверка доступа ───────────────────────────────────────────────────


def check_access(update: Update) -> bool:
    """Проверяет, что сообщение от владельца или доверенного админа."""
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        print(f"⛔ Доступ запрещён: user={user.id} (@{user.username})")
        return False
    return True


# ── Утилиты ────────────────────────────────────────────────────────────


def run_script(script: str, args: list[str] = None) -> str:
    """Запускает Python-скрипт и возвращает результат."""
    script_path = os.path.join(PROJECT_DIR, "agents", script)
    if not os.path.exists(script_path):
        return f"❌ Файл не найден: agents/{script}"

    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    result = subprocess.run(
        cmd, cwd=PROJECT_DIR, capture_output=True, text=True, timeout=300
    )
    output = result.stdout.strip()[-2000:] if result.stdout else ""

    if result.returncode == 0:
        return (
            f"✅ {script} выполнен успешно\n\n{output}"
            if output
            else f"✅ {script} выполнен успешно"
        )
    else:
        return (
            f"❌ {script} ошибка (код {result.returncode})\n\n{result.stderr[-500:]}"
            if result.stderr
            else f"❌ {script} ошибка (код {result.returncode})"
        )


def get_file_preview(path: str, lines: int = 10) -> str:
    """Читает первые строки файла."""
    full_path = os.path.join(PROJECT_DIR, path)
    if not os.path.exists(full_path):
        return f"❌ {path} не найден"
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()
    preview = "\n".join(content.split("\n")[:lines])
    return f"📄 {path}:\n{preview}..."


def list_recent_files() -> str:
    """Показывает последние созданные файлы."""
    files = []
    for root, _, filenames in os.walk(PROJECT_DIR):
        for fn in filenames:
            if fn.endswith(".md") and not root.endswith("site"):
                full = os.path.join(root, fn)
                rel = os.path.relpath(full, PROJECT_DIR)
                mtime = os.path.getmtime(full)
                files.append((mtime, rel))

    files.sort(reverse=True)
    lines = ["📁 Последние файлы:\n"]
    for mtime, name in files[:10]:
        dt = datetime.fromtimestamp(mtime).strftime("%d.%m %H:%M")
        lines.append(f"  {dt}  {name}")
    return "\n".join(lines)


# ── Обработчики команд ─────────────────────────────────────────────────


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return
    await update.message.reply_text(
        "👋 Привет, командующий!\n\n"
        "Доступные команды:\n"
        "/status — статус команды\n"
        "/content — статьи и посты\n"
        "/run — запустить оркестратор\n"
        "/post [текст] — публикация в канал\n"
        "/test [текст] — пробный пост (в чат)\n"
        "/post_now [текст] — экстренная публикация\n"
        "/report — недельный отчёт\n"
        "/report_now — принудительный отчёт\n"
        "/archive — сохранить посты в Obsidian\n"
        "/brain — второй мозг (Obsidian)"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    reply = list_recent_files()
    reply += "\n\n🤖 Агенты:\n"
    reply += "  ✅ CMO Agent (cmo_agent.py)\n"
    reply += "  ✅ Content Writer (content_writer.py)\n"
    reply += "  ✅ Telegram Agent (telegram_agent.py)\n"
    reply += "  ✅ Telegram Bot (telegram_bot.py)\n"
    reply += "\n🚀 Оркестратор: orchestrator.py"

    await update.message.reply_text(reply)


async def content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    reply = ""
    for i in [1, 2]:
        preview = get_file_preview(f"blog/article-{i}.md", 5)
        reply += f"{preview}\n\n"

    reply += "📱 Telegram-посты:\n"
    for i in [1, 2]:
        full = os.path.join(PROJECT_DIR, f"telegram/post-{i}.md")
        if os.path.exists(full):
            with open(full) as f:
                text = f.read()
            reply += f"\npost-{i}.md: {'✅' if len(text) > 100 else '⚠️'}"
        else:
            reply += f"\npost-{i}.md: ❌"

    await update.message.reply_text(reply[:4000])


async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    await update.message.reply_text("🚀 Запускаю orchestrator.py --no-telegram...")
    result = run_script("cmo_agent.py")
    await update.message.reply_text(result[:2000])

    result = run_script("content_writer.py")
    await update.message.reply_text(result[:2000])

    result = run_script("telegram_agent.py", ["--plan-only"])
    await update.message.reply_text(
        result[:2000] + "\n\n✅ Все агенты отработали. Файлы обновлены."
    )


async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("❌ Укажите текст: /post Ваш текст здесь")
        return

    if not CHANNEL_ID:
        await update.message.reply_text("❌ TELEGRAM_CHANNEL_ID не задан в .env")
        return

    allowed, next_date = can_post()
    if not allowed:
        await update.message.reply_text(
            f"⏳ Постинг раз в неделю. Следующий пост: {next_date}"
        )
        return

    import requests

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text[:4096]}
    r = requests.post(url, json=payload, timeout=15)

    if r.status_code == 200:
        mark_posted()
        await update.message.reply_text(f"✅ Опубликовано в канале:\n\n{text[:500]}")
    else:
        await update.message.reply_text(f"❌ Ошибка Telegram API: {r.json()}")


async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерирует пост в стиле канала с 3 вариантами картинок."""
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    text = " ".join(context.args) if context.args else ""

    from dotenv import load_dotenv
    from openai import OpenAI

    if text:
        await update.message.reply_text(f"🧪 Твой текст:\n\n{text[:2000]}")
        return

    chat_id = str(update.effective_chat.id)

    # Проверяем кеш — если уже есть готовый пост, показываем его
    if "post_cache" not in context.bot_data:
        context.bot_data["post_cache"] = {}
    cache = context.bot_data["post_cache"]

    # Генерируем новый пост если нет в кеше или нажали /test
    await update.message.reply_text("✍️ Генерирую пост в стиле канала...")

    # Читаем гайд по стилю
    style_path = os.path.join(PROJECT_DIR, "STYLE_GUIDE.md")
    style = ""
    if os.path.exists(style_path):
        with open(style_path) as f:
            style = f.read()

    # Выбираем тему (только детская психология)
    import json
    import random

    topic_text = "Напиши пост для канала на тему детской психологии, воспитания, отношений с детьми."
    topics_file = os.path.join(PROJECT_DIR, "post_topics.json")
    if os.path.exists(topics_file):
        with open(topics_file) as f:
            all_topics = json.load(f)
        # Фильтруем: только темы по детской психологии
        child_keywords = [
            "ребён",
            "дети",
            "подрост",
            "школ",
            "матер",
            "родител",
            "детск",
            "семь",
            "мам",
            "воспит",
        ]
        filtered = [
            t
            for t in all_topics
            if any(kw in t["topic"].lower() for kw in child_keywords)
        ]
        if filtered:
            chosen = random.choice(filtered)
            topic_text = f"Напиши пост на тему детской психологии: {chosen['topic']}"

    load_dotenv()
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com"
    )

    system_prompt = f"""Ты — психолог Анастасия Палютина. Напиши пост для Telegram-канала.

Твой стиль:
{style}

Требования:
- 500-1500 знаков
- Тёплый, доверительный тон
- Одна конкретная мысль
- Призыв к взаимодействию в конце
- ВАЖНО: сегодня {datetime.now().strftime("%A")}. Ссылайся на следующий пост в пятницу или вторник.
- Тема: детская психология, воспитание, отношения с детьми и подростками"""

    r = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": topic_text},
        ],
        temperature=0.7,
        max_tokens=1500,
    )
    post = r.choices[0].message.content or "Не удалось сгенерировать"

    # Генерируем 3 варианта картинок
    await update.message.reply_text("🎨 Генерирую 3 варианта картинок...")
    import urllib.parse

    image_urls = []
    for i in range(3):
        img_prompt = (
            f"minimalist abstract illustration for psychology post: {post[:200]}. "
            f"soft pastel colors beige sage-blue calm atmosphere. "
            f"NO people NO faces NO hands NO text. Clean simple composition. "
            f"style: flat vector illustration scandinavian design. variant {i + 1}"
        )
        img_r = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "Ты — AI-арт-директор. Кратко опиши изображение на английском.",
                },
                {"role": "user", "content": img_prompt},
            ],
            temperature=0.8,
            max_tokens=150,
        )
        img_desc = img_r.choices[0].message.content.strip()
        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(img_desc)}?width=768&height=768&nologo=true&model=flux"
        image_urls.append({"url": img_url, "desc": img_desc})

    # Сохраняем в кеш для /edit и /ok
    cache[chat_id] = {"post": post, "images": image_urls, "chosen_image": 0}

    # Показываем 3 картинки
    for i, img in enumerate(image_urls):
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"✅ Выбрать картинку {i + 1}", callback_data=f"pick_img_{i}"
                    ),
                ]
            ]
        )
        try:
            await update.message.reply_photo(
                photo=img["url"],
                caption=f"🖼️ Вариант {i + 1}",
                reply_markup=kb,
                read_timeout=20,
            )
        except Exception:
            await update.message.reply_text(
                f"🖼️ Вариант {i + 1}: {img['url']}", reply_markup=kb
            )

    # Отправляем текст с кнопками действий
    action_kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Опубликовать", callback_data="approve"),
                InlineKeyboardButton("⏭️ Пропустить", callback_data="skip"),
                InlineKeyboardButton("✏️ Редактировать", callback_data="edit"),
            ]
        ]
    )
    await update.message.reply_text(
        f"📝 Текст поста:\n\n{post[:4000]}", reply_markup=action_kb
    )

    await update.message.reply_text(
        "👆 Выберите картинку (нажмите на вариант), затем действие."
    )


# ── Обработчик inline-кнопок ─────────────────────────────────────────


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки: ок, скип, эдит, выбор картинки."""
    query = update.callback_query
    data = query.data
    chat_id = str(query.message.chat_id)

    cache = context.bot_data.get("post_cache", {})
    entry = cache.get(chat_id, {})
    post = entry.get("post", "")

    if not post:
        await query.answer("Нет активного поста. Запустите /test")
        return

    if data.startswith("pick_img_"):
        idx = int(data.replace("pick_img_", ""))
        entry["chosen_image"] = idx
        cache[chat_id] = entry
        await query.answer(f"✅ Выбрана картинка {idx + 1}")
        kb = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🔄 Изменить картинку", callback_data=f"edit_img_{idx}"
                    ),
                    InlineKeyboardButton("✅ Ок, дальше", callback_data="img_ok"),
                ]
            ]
        )
        await query.message.edit_reply_markup(reply_markup=kb)

    elif data.startswith("edit_img_"):
        idx = int(data.replace("edit_img_", ""))
        entry["editing_image"] = idx
        cache[chat_id] = entry
        await query.message.reply_text(
            '🎨 Опишите что изменить на картинке (например: "добавь больше синего", "сделай светлее")'
        )

    elif data == "img_ok":
        await query.answer("Картинка выбрана. Теперь нажмите действие под текстом.")

    elif data == "approve":
        # Публикуем в канал
        import requests

        img_idx = entry.get("chosen_image", 0)
        img_url = entry["images"][img_idx]["url"]

        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        payload = {"chat_id": CHANNEL_ID, "photo": img_url, "caption": post[:1024]}
        r = requests.post(url, json=payload, timeout=15)

        if r.status_code == 200:
            mark_posted()
            await query.message.edit_text(f"✅ Опубликовано в канале!\n\n{post[:500]}")
            cache.pop(chat_id, None)
        else:
            await query.answer(f"❌ Ошибка: {r.json()}")

    elif data == "skip":
        cache.pop(chat_id, None)
        await query.message.edit_text("⏭️ Пост пропущен.")

    elif data == "edit":
        entry["editing"] = True
        cache[chat_id] = entry
        await query.message.reply_text(
            "✏️ Отправьте исправленный текст одним сообщением.\n\nТекущий текст:\n\n"
            + post[:1500]
        )

    await query.answer()


async def post_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    text = " ".join(context.args) if context.args else (update.message.caption or "")
    if not text and not update.message.photo:
        await update.message.reply_text(
            "❌ Отправьте текст или фото с подписью: /post_now Ваш текст"
        )
        return

    if not CHANNEL_ID:
        await update.message.reply_text("❌ TELEGRAM_CHANNEL_ID не задан в .env")
        return

    allowed, next_date = can_post()
    if not allowed:
        await update.message.reply_text(
            f"⏳ Постинг раз в неделю. Следующий пост: {next_date}"
        )
        return

    import requests

    sent = False
    if update.message.photo:
        # Отправляем фото с подписью
        photo = update.message.photo[-1]  # Max resolution
        file_url = (
            f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={photo.file_id}"
        )
        file_data = requests.get(file_url).json()
        file_path = file_data.get("result", {}).get("file_path")
        if file_path:
            photo_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
            payload = {
                "chat_id": CHANNEL_ID,
                "photo": photo_url,
                "caption": text[:1024] if text else "",
            }
            r = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                json=payload,
                timeout=15,
            )
            sent = r.status_code == 200

    if not sent and text:
        # Отправляем текст
        payload = {"chat_id": CHANNEL_ID, "text": text[:4096]}
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage", json=payload, timeout=15
        )
        sent = r.status_code == 200

    if sent:
        mark_posted()
        await update.message.reply_text(
            f"🚨 Экстренная публикация!\n✅ Отправлено в канал"
        )
    else:
        await update.message.reply_text(f"❌ Ошибка отправки")


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    await update.message.reply_text("📊 Запрашиваю недельный отчёт...")
    result = run_script("cmo_agent.py", ["--weekly"])
    await update.message.reply_text(result[:4000])


async def archive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет посты из канала в Obsidian для анализа."""
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    import json
    from datetime import datetime

    import requests

    cache_file = os.path.join(PROJECT_DIR, "channel_cache.json")
    if not os.path.exists(cache_file):
        await update.message.reply_text(
            "📭 Кеш канала пуст. Бот ещё не получал посты из канала. Добавьте бота админом в канал и напишите туда что-нибудь."
        )
        return

    with open(cache_file) as f:
        posts = json.load(f)

    if not posts:
        await update.message.reply_text("📭 Постов нет.")
        return

    vault = "/Users/dmitrii/ИИ/2й Поток/Brain/wiki/marketing/archived"
    os.makedirs(vault, exist_ok=True)

    saved = 0
    for post in posts[-20:]:
        dt = datetime.fromtimestamp(post["date"]).strftime("%Y-%m-%d-%H%M")
        filename = f"{vault}/post-{dt}.md"
        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write(
                    f"# Пост от {datetime.fromtimestamp(post['date']).strftime('%d.%m.%Y %H:%M')}\n\n{post['text']}\n"
                )
            saved += 1

    await update.message.reply_text(
        f"✅ {saved} новых постов сохранено в Obsidian: wiki/marketing/archived/"
    )


# ── Approval system: /ok и /skip ─────────────────────────────────────


async def ok_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Одобряет отложенный пост и публикует в канал."""
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    import json

    import requests

    if not os.path.exists(PENDING_FILE):
        await update.message.reply_text("📭 Нет постов на утверждении.")
        return

    with open(PENDING_FILE) as f:
        pending = json.load(f)

    if not pending:
        await update.message.reply_text("📭 Нет постов на утверждении.")
        return

    post = pending.pop(0)
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f)

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": post["text"][:4096]}
    r = requests.post(url, json=payload, timeout=15)

    if r.status_code == 200:
        mark_posted()
        await update.message.reply_text(
            f"✅ Опубликовано в канале:\n\n{post['text'][:500]}"
        )
    else:
        await update.message.reply_text(f"❌ Ошибка публикации: {r.json()}")


async def skip_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропускает отложенный пост (не публикует)."""
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    import json

    if not os.path.exists(PENDING_FILE):
        await update.message.reply_text("📭 Нет постов на утверждении.")
        return

    with open(PENDING_FILE) as f:
        pending = json.load(f)

    if not pending:
        await update.message.reply_text("📭 Нет постов на утверждении.")
        return

    skipped = pending.pop(0)
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f)

    await update.message.reply_text(
        f"⏭️ Пропущен:\n\n{skipped['text'][:300]}\n\nОсталось на утверждении: {len(pending)}"
    )


async def report_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    await update.message.reply_text("📊 Принудительный отчёт...")
    result = run_script("cmo_agent.py", ["--weekly"])
    await update.message.reply_text(
        result[:4000] + "\n\n⚡ Отчёт сформирован вне расписания."
    )


async def brain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает содержимое второго мозга (Obsidian)."""
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_DIR, "agents", "second_brain.py")],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=10,
    )
    await update.message.reply_text(result.stdout[:4000])


# ── Сбор примеров постов для /learn ─────────────────────────────────


async def learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Анализирует стиль постов через DeepSeek."""
    if not check_access(update):
        await update.message.reply_text("⛔ Access denied")
        return

    style_file = os.path.join(PROJECT_DIR, "style_examples.json")
    if not os.path.exists(style_file):
        await update.message.reply_text(
            "📭 Нет примеров. Перешлите 3-5 постов, затем /learn."
        )
        return

    import json

    with open(style_file) as f:
        examples = json.load(f)

    if len(examples) < 2:
        await update.message.reply_text(
            f"Нужно хотя бы 2 поста. Сейчас: {len(examples)}."
        )
        return

    await update.message.reply_text(f"🧠 Анализирую {len(examples)} постов...")

    result = subprocess.run(
        [sys.executable, os.path.join(PROJECT_DIR, "agents", "style_learner.py")],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode == 0 and "OK" in result.stdout:
        guide = result.stdout.split("OK:", 1)[-1].strip()
        await update.message.reply_text(
            f"✅ Стиль проанализирован!\n\n{guide[:2000]}\n\nСохранено: Obsidian/wiki/marketing/style-guide.md"
        )
    else:
        await update.message.reply_text(
            f"❌ Ошибка: {result.stderr[:300] or result.stdout[:300]}"
        )


# ── Планировщик: еженедельный отчёт ────────────────────────────────────


async def weekly_report_job(context: ContextTypes.DEFAULT_TYPE):
    """Запускает weekly_reporter.py и отправляет пост на утверждение."""
    print("\n📊 [Scheduler] Запуск Weekly Reporter...")
    result = subprocess.run(
        [
            sys.executable,
            os.path.join(PROJECT_DIR, "agents", "weekly_reporter.py"),
        ],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )

    import json

    # Читаем сгенерированный пост
    post_file = os.path.join(PROJECT_DIR, "telegram", "post-1.md")
    post_text = ""
    if os.path.exists(post_file):
        with open(post_file) as f:
            post_text = f.read()[:2000]
    else:
        post_text = f"📊 Недельный отчёт готов.\n\n{result.stdout[-1500:]}"

    # Сохраняем в очередь на утверждение
    pending = []
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE) as f:
            pending = json.load(f)
    pending.append({"text": post_text, "date": datetime.now().isoformat()})
    with open(PENDING_FILE, "w") as f:
        json.dump(pending, f)

    # Уведомляем админов
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"📊 Пост на утверждение:\n\n{post_text[:500]}\n\n/ok — опубликовать\n/skip — пропустить",
            )
        except Exception as e:
            print(f"Не удалось уведомить {admin_id}: {e}")


# ── Обработка неизвестных пользователей ────────────────────────────────


async def handle_unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Любое сообщение от не-владельца → Access denied."""
    user = update.effective_user
    print(f"⛔ Неизвестный: user={user.id} (@{user.username})")
    await update.message.reply_text("⛔ Access denied")


# ── Запуск бота ────────────────────────────────────────────────────────


def main():
    print("=" * 50)
    print("🤖 Telegram Bot — запуск")
    print(f"   Админы ID: {USER_IDS_RAW}")
    print(f"   Канал ID: {CHANNEL_ID}")
    print("=" * 50)

    app = Application.builder().token(TOKEN).build()

    # Команды — только для владельца (проверка внутри каждого handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("content", content))
    app.add_handler(CommandHandler("run", run_cmd))
    app.add_handler(CommandHandler("post", post))
    app.add_handler(CommandHandler("test", test))
    app.add_handler(CommandHandler("post_now", post_now))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("report_now", report_now))
    app.add_handler(CommandHandler("brain", brain))
    app.add_handler(CommandHandler("archive", archive))
    app.add_handler(CommandHandler("ok", ok_cmd))
    app.add_handler(CommandHandler("skip", skip_cmd))
    app.add_handler(CommandHandler("learn", learn))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Сохраняем текстовые сообщения для /learn и /edit
    async def save_forward(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_access(update):
            return
        msg = update.message
        if msg and msg.text:
            chat_id = str(update.effective_chat.id)
            cache = context.bot_data.get("post_cache", {})
            entry = cache.get(chat_id, {})

            # Если режим редактирования картинки
            if entry.get("editing_image") is not None:
                idx = entry["editing_image"]
                edit_prompt = msg.text
                entry["editing_image"] = None

                # Регенерируем картинку с учётом правок
                from dotenv import load_dotenv
                from openai import OpenAI

                load_dotenv()
                client = OpenAI(
                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                    base_url="https://api.deepseek.com",
                )
                old_desc = entry["images"][idx]["desc"]
                img_prompt = f"Modify the image: {old_desc}. Change: {edit_prompt}. Same style, pastel tones, no faces. English only."
                img_r = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": img_prompt}],
                    temperature=0.7,
                    max_tokens=150,
                )
                import urllib.parse

                new_desc = img_r.choices[0].message.content.strip()
                new_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(new_desc)}?width=768&height=768&nologo=true&model=flux"
                entry["images"][idx] = {"url": new_url, "desc": new_desc}
                cache[chat_id] = entry

                kb = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                f"✅ Выбрать обновлённую картинку",
                                callback_data=f"pick_img_{idx}",
                            ),
                        ]
                    ]
                )
                try:
                    await update.message.reply_photo(
                        photo=new_url,
                        caption=f"🔄 Обновлённая картинка (изменено: {edit_prompt})",
                        reply_markup=kb,
                        read_timeout=20,
                    )
                except Exception:
                    await update.message.reply_text(
                        f"🔄 Обновлённая картинка: {new_url}", reply_markup=kb
                    )
                return

            # Если режим редактирования текста — обновляем пост
            if entry.get("editing"):
                entry["post"] = msg.text
                entry["editing"] = False
                cache[chat_id] = entry
                action_kb = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "✅ Опубликовать", callback_data="approve"
                            ),
                            InlineKeyboardButton("⏭️ Пропустить", callback_data="skip"),
                            InlineKeyboardButton(
                                "✏️ Редактировать", callback_data="edit"
                            ),
                        ]
                    ]
                )
                await update.message.reply_text(
                    f"✅ Текст обновлён!\n\n{msg.text[:4000]}", reply_markup=action_kb
                )
                return

            # Иначе сохраняем как пример стиля
            if len(msg.text.strip()) > 50:
                import json

                style_file = os.path.join(PROJECT_DIR, "style_examples.json")
                examples = []
                if os.path.exists(style_file):
                    with open(style_file) as f:
                        examples = json.load(f)
                examples.append({"text": msg.text, "date": datetime.now().isoformat()})
                if len(examples) > 20:
                    examples = examples[-20:]
                with open(style_file, "w") as f:
                    json.dump(examples, f)
                await update.message.reply_text(
                    f"📥 Сохранён. Примеров: {len(examples)}."
                )

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_forward))

    # Сохраняем темы для постов
    async def save_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not check_access(update):
            return
        msg = update.message
        if msg and msg.text and msg.text.startswith("/topic"):
            topics = msg.text.replace("/topic", "", 1).strip()
            if not topics:
                await update.message.reply_text(
                    "❌ Укажите тему: /topic Как справиться с выгоранием"
                )
                return
            import json

            tf = os.path.join(PROJECT_DIR, "post_topics.json")
            existing = []
            if os.path.exists(tf):
                with open(tf) as f:
                    existing = json.load(f)
            existing.append({"topic": topics, "date": datetime.now().isoformat()})
            with open(tf, "w") as f:
                json.dump(existing[-50:], f)
            await update.message.reply_text(
                f"📝 Тема сохранена. Всего тем: {len(existing)}\nПри /test бот выберет случайную тему."
            )

    app.add_handler(CommandHandler("topic", save_topic))

    # Кешируем посты из канала для /archive
    async def cache_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.channel_post:
            import json as j

            cache_file = os.path.join(PROJECT_DIR, "channel_cache.json")
            posts = []
            if os.path.exists(cache_file):
                with open(cache_file) as f:
                    posts = j.load(f)
            posts.append(
                {
                    "date": update.channel_post.date.timestamp(),
                    "text": update.channel_post.text or "",
                }
            )
            with open(cache_file, "w") as f:
                j.dump(posts[-500:], f)  # Храним последние 500

    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POST, cache_channel))

    # Все остальные сообщения → проверка владельца
    app.add_handler(MessageHandler(filters.ALL, handle_unknown))

    # ── Планировщик: вторник и пятница в 20:00 ──
    app.job_queue.run_daily(
        weekly_report_job,
        time=time(hour=20, minute=0),
        days=(1, 4),  # Tuesday, Friday
    )
    print("📅 Планировщик: пост на утверждение → вторник и пятница в 20:00")

    print("✅ Бот запущен. Нажмите Ctrl+C для остановки.\n")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
