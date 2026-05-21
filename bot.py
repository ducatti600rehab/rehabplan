import os
import json
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes
import httpx

API_KEY = "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"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8542678279:AAGoe8zMJtw_ZQkM-m0Z46rN5FhUBcvx_Io")

# States
DIAG, STAGE, LOC, PERIOD, AGE, EQUIP, CONTRA, NOTES, CONFIRM = range(9)

DIAG_MAP = {
    "1": ("lymph-upper", "Лимфостаз верхних конечностей (постмастэктомия)"),
    "2": ("stiff-joint", "Тугоподвижность суставов без лимфостаза"),
    "3": ("lymph-stiff", "Лимфостаз + тугоподвижность"),
    "4": ("lymph-lower", "Лимфостаз нижних конечностей"),
}
STAGE_MAP = {"1": "I (преходящий)", "2": "II (стойкий)", "3": "III (слоновость)", "0": "нет/не применимо"}
PER_MAP = {"1": "острый (до 3 мес.)", "2": "подострый (3–12 мес.)", "3": "хронический (>12 мес.)"}

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text(
        "👋 RehabPlan — планировщик реабилитации\n\n"
        "Выберите основной диагноз:\n"
        "1️⃣ Лимфостаз верхних конечностей (постмастэктомия)\n"
        "2️⃣ Тугоподвижность суставов без лимфостаза\n"
        "3️⃣ Лимфостаз + тугоподвижность\n"
        "4️⃣ Лимфостаз нижних конечностей\n\n"
        "Отправьте цифру:",
        reply_markup=ReplyKeyboardMarkup([["1","2"],["3","4"]], resize_keyboard=True)
    )
    return DIAG

async def get_diag(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val not in DIAG_MAP:
        await update.message.reply_text("Отправьте цифру от 1 до 4")
        return DIAG
    ctx.user_data["diag"] = DIAG_MAP[val]
    await update.message.reply_text(
        "Стадия лимфостаза:\n0 — нет/не применимо\n1 — I преходящий\n2 — II стойкий\n3 — III слоновость",
        reply_markup=ReplyKeyboardMarkup([["0","1"],["2","3"]], resize_keyboard=True)
    )
    return STAGE

async def get_stage(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val not in STAGE_MAP:
        await update.message.reply_text("Отправьте цифру 0-3")
        return STAGE
    ctx.user_data["stage"] = STAGE_MAP[val]
    await update.message.reply_text(
        "Локализация поражения:\n1 — Правая рука\n2 — Левая рука\n3 — Обе руки\n"
        "4 — Правая нога\n5 — Левая нога\n6 — Обе ноги\n7 — Плечевой сустав\n8 — Коленный сустав",
        reply_markup=ReplyKeyboardMarkup([["1","2","3"],["4","5","6"],["7","8"]], resize_keyboard=True)
    )
    return LOC

LOC_MAP = {"1":"Правая рука","2":"Левая рука","3":"Обе руки","4":"Правая нога","5":"Левая нога","6":"Обе ноги","7":"Плечевой сустав","8":"Коленный сустав"}

async def get_loc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val not in LOC_MAP:
        await update.message.reply_text("Отправьте цифру 1-8")
        return LOC
    ctx.user_data["loc"] = LOC_MAP[val]
    await update.message.reply_text(
        "Период после лечения:\n1 — Острый (до 3 мес.)\n2 — Подострый (3–12 мес.)\n3 — Хронический (>12 мес.)",
        reply_markup=ReplyKeyboardMarkup([["1","2","3"]], resize_keyboard=True)
    )
    return PERIOD

async def get_period(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val not in PER_MAP:
        await update.message.reply_text("Отправьте цифру 1-3")
        return PERIOD
    ctx.user_data["period"] = PER_MAP[val]
    await update.message.reply_text(
        "Возраст пациентки (лет):\nНапример: 52",
        reply_markup=ReplyKeyboardMarkup([["Пропустить"]], resize_keyboard=True)
    )
    return AGE

async def get_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    ctx.user_data["age"] = val if val != "Пропустить" else "не указан"
    await update.message.reply_text(
        "Доступное оборудование (можно несколько через запятую):\n"
        "1 — Пневмокомпрессия\n2 — Лазер (рлазер)\n3 — НЧМТ\n"
        "4 — Мануальный лимфодренаж\n5 — Зал ЛФК\n6 — Механотерапия\n"
        "7 — Бассейн\n8 — Компрессионный бандаж\n\nПример: 1,2,3,4,5,6",
        reply_markup=ReplyKeyboardMarkup([["1,2,3,4,5,6"],["1,2,3,4,5"]], resize_keyboard=True)
    )
    return EQUIP

EQUIP_MAP = {"1":"Пневмокомпрессия","2":"Лазер","3":"НЧМТ","4":"Мануальный лимфодренаж","5":"Зал ЛФК","6":"Механотерапия","7":"Бассейн","8":"Компрессионный бандаж"}

async def get_equip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    parts = [v.strip() for v in val.split(",")]
    equip = [EQUIP_MAP[p] for p in parts if p in EQUIP_MAP]
    ctx.user_data["equip"] = ", ".join(equip) if equip else "стандартный зал ЛФК"
    await update.message.reply_text(
        "Противопоказания (цифры через запятую или 0 — нет):\n"
        "1 — Активный онкопроцесс\n2 — Тромбоз/ТЭЛА\n3 — Рожистое воспаление\n"
        "4 — СН IIб–III\n5 — ХБП III–V\n6 — Металлоконструкции\n"
        "7 — Кардиостимулятор\n8 — АГ ≥180/110",
        reply_markup=ReplyKeyboardMarkup([["0"],["1,2"],["3,4"]], resize_keyboard=True)
    )
    return CONTRA

CONTRA_MAP = {"1":"Активный онкопроцесс","2":"Тромбоз/ТЭЛА","3":"Рожистое воспаление","4":"СН IIб–III","5":"ХБП III–V","6":"Металлоконструкции","7":"Кардиостимулятор","8":"АГ ≥180/110"}

async def get_contra(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if val == "0":
        ctx.user_data["contra"] = "нет"
    else:
        parts = [v.strip() for v in val.split(",")]
        contra = [CONTRA_MAP[p] for p in parts if p in CONTRA_MAP]
        ctx.user_data["contra"] = ", ".join(contra) if contra else "нет"
    await update.message.reply_text(
        "Дополнительные сведения (боль, сопутствующие заболевания):\nИли нажмите Пропустить",
        reply_markup=ReplyKeyboardMarkup([["Пропустить"]], resize_keyboard=True)
    )
    return NOTES

async def get_notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    ctx.user_data["notes"] = val if val != "Пропустить" else "нет"
    d = ctx.user_data
    summary = (
        f"📋 Проверьте данные:\n\n"
        f"Диагноз: {d['diag'][1]}\n"
        f"Стадия: {d['stage']}\n"
        f"Локализация: {d['loc']}\n"
        f"Период: {d['period']}\n"
        f"Возраст: {d['age']}\n"
        f"Оборудование: {d['equip']}\n"
        f"Противопоказания: {d['contra']}\n"
        f"Доп. сведения: {d['notes']}\n\n"
        f"Сформировать комплекс?"
    )
    await update.message.reply_text(
        summary,
        reply_markup=ReplyKeyboardMarkup([["✅ Да, сформировать"],["🔄 Начать заново"]], resize_keyboard=True)
    )
    return CONFIRM

async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if "заново" in val:
        return await start(update, ctx)
    
    await update.message.reply_text("⏳ Формируем комплекс... (30-60 секунд)")
    
    d = ctx.user_data
    diag_key = d["diag"][0]
    
    profile_hint = ""
    if diag_key == "lymph-upper":
        profile_hint = "Постмастэктомический синдром: приоритет — редукция отёка руки, восстановление ротации плеча. Последовательность: лимфодренаж → ЛФК → механотерапия → физиотерапия."
    elif diag_key == "stiff-joint":
        profile_hint = "Тугоподвижность без лимфостаза: акцент на мобилизацию сустава и механотерапию для восстановления амплитуды."
    elif diag_key == "lymph-stiff":
        profile_hint = "Комбинация: сначала редукция отёка, затем мобилизация. Механотерапию начинать после уменьшения отёка."

    mech_hint = "Включи блок механотерапии верхней конечности (3-4 позиции на блоковых/маятниковых тренажёрах) если есть в оборудовании." if "Механотерапия" in d["equip"] else ""

    prompt = f"""Ты эксперт-реабилитолог по лимфостазу и тугоподвижности после онкологического лечения.

КЛИНИКА:
Диагноз: {d['diag'][1]}
Стадия лимфостаза: {d['stage']}
Локализация: {d['loc']}
Период: {d['period']}
Возраст: {d['age']}
Оборудование: {d['equip']}
Противопоказания: {d['contra']}
Доп. сведения: {d['notes']}

{profile_hint}
{mech_hint}

Составь реабилитационный комплекс. Формат ответа — текст для Telegram (без JSON, без markdown таблиц).
Структура:
🎯 ТАКТИКА
(2-3 предложения)

🏃 ЛФК (6+ упражнений)
— Название: техника, дозировка, частота

⚙️ МЕХАНОТЕРАПИЯ (если есть оборудование)
— Тренажёр: техника, нагрузка, дозировка

💧 ЛИМФОДРЕНАЖ
— Метод: техника, длительность, частота

⚡ ФИЗИОТЕРАПИЯ (только из доступного оборудования)
— Метод: параметры, зона, курс

📅 НЕДЕЛЬНЫЙ ГРАФИК

📊 МОНИТОРИНГ

При противопоказаниях ({d['contra']}) строго исключи соответствующие методы."""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 3000,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            data = resp.json()
            text = data["content"][0]["text"]
            
            # Split long messages for Telegram (max 4096 chars)
            while len(text) > 4000:
                chunk = text[:4000]
                last_newline = chunk.rfind('\n')
                if last_newline > 0:
                    chunk = text[:last_newline]
                await update.message.reply_text(chunk)
                text = text[len(chunk):]
            
            if text:
                await update.message.reply_text(
                    text + "\n\n⚠️ Комплекс носит рекомендательный характер. Корректировка — за врачом-реабилитологом.",
                    reply_markup=ReplyKeyboardMarkup([["🔄 Новый пациент"]], resize_keyboard=True)
                )
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}\nПопробуйте /start")
    
    return ConversationHandler.END

async def new_patient(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    return await start(update, ctx)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.Regex("Новый пациент"), start)],
        states={
            DIAG: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_diag)],
            STAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stage)],
            LOC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_loc)],
            PERIOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_period)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            EQUIP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_equip)],
            CONTRA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contra)],
            NOTES: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_notes)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    
    app.add_handler(conv)
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
