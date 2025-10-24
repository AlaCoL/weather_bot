import requests
import datetime
import dateparser
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "7047947994:AAGqnklImKWS-fAmamMHe_ym3w3WfW_TSx4"
OPENWEATHER_API_KEY = "b22d4ca7ac9bdb012661cc54af5ec7b2"

CITY_CORRECTIONS = {
    "москве": "москва",
    "астане": "астана",
    "алматы": "алматы",
    "санкт-петербурге": "санкт-петербург",
    "новосибирске": "новосибирск",
    "екатеринбурге": "екатеринбург",
    "омске": "омск",
    "тбилиси": "тбилиси",
}

def normalize_city(city: str) -> str:
    city = city.strip().lower()
    if city in CITY_CORRECTIONS:
        return CITY_CORRECTIONS[city]
    if city.endswith(("е", "и", "у", "ю")) and len(city) > 4:
        city = city[:-1]
    return city

def get_weather(city: str, target_time: datetime.datetime):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    r = requests.get(url)
    if r.status_code != 200:
        return f"Не удалось получить данные о погоде для города '{city}'. 😅"

    data = r.json()
    if data.get("cod") != "200":
        return f"Не удалось найти город '{city}'."

    forecasts = data.get("list", [])
    if not forecasts:
        return "Прогноз недоступен."

    best = min(forecasts, key=lambda x: abs(datetime.datetime.fromtimestamp(x["dt"]) - target_time))
    temp = best["main"]["temp"]
    desc = best["weather"][0]["description"]
    time_txt = datetime.datetime.fromtimestamp(best["dt"]).strftime("%d.%m %H:%M")

    return f"{city.title()} — прогноз на {time_txt}: {temp:.1f}°C, {desc}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 🌦 Напиши, например:\n"
        "• Какая температура завтра в Москве?\n"
        "• Погода через 3 часа в Астане?\n"
        "• Что будет через неделю в Алматы?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    match = re.search(r"(?:в|во)\s+([а-яёa-z\-\s]+)", text)
    city = match.group(1).strip() if match else "Алматы"
    city = normalize_city(city)

    parsed_time = dateparser.parse(text, languages=["ru"], settings={"PREFER_DATES_FROM": "future"})
    if not parsed_time:
        parsed_time = datetime.datetime.now() + datetime.timedelta(hours=3)
        note = "Не понял, на какое время — показываю ближайшие 3 часа.\n"
    else:
        note = ""

    try:
        weather = get_weather(city, parsed_time)
    except Exception as e:
        weather = f"Ошибка при получении данных: {e}"

    await update.message.reply_text(note + weather)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен! Можно спрашивать, например: 'Какая температура завтра в Москве?'")
    app.run_polling()

if __name__ == "__main__":
    main()