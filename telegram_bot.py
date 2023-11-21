import asyncio
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
    MessageHandler,
)

import logging

import multiprocessing
import subprocess
import datetime
import kleinanzeigenbot

BOT_TOKEN = "6616611678:AAEVGAnVbc2w2biSU4JqvI9m-KA5hq_4pm8"

# Definieren Sie Konstanten für die verschiedenen Stadien der Konversation
(
    SEARCH_TERM,
    SEARCH_SLEEP_TIME,
    SEARCH_CATEGORY,
    SEARCH_PRICE_MIN,
    SEARCH_PRICE_MAX,
) = range(5)

worker_processes = []
current_worker_id = 0
message_bus_queue = multiprocessing.Queue()
chat_ids_for_notifications = set()

main_categories = [
    {"title": "Auto, Rad & Boot", "callback_data": "category_main_210"},
    {"title": "Dienstleistungen", "callback_data": "category_main_297"},
    {"title": "Eintrittskarten & Tickets", "callback_data": "category_main_231"},
    {"title": "Elektronik", "callback_data": "category_main_161"},
    {"title": "Familie, Kind & Baby", "callback_data": "category_main_17"},
    {"title": "Freizeit, Hobby & Nachbarschaft", "callback_data": "category_main_185"},
    {"title": "Haus & Garten", "callback_data": "category_main_80"},
    {"title": "Haustiere", "callback_data": "category_main_130"},
    {"title": "Immobilien", "callback_data": "category_main_195"},
    {"title": "Jobs", "callback_data": "category_main_102"},
    {"title": "Mode & Beauty", "callback_data": "category_main_153"},
    {"title": "Musik, Filme & Bücher", "callback_data": "category_main_73"},
    {"title": "Nachbarschaftshilfe", "callback_data": "category_main_400"},
    {"title": "Unterricht & Kurse", "callback_data": "category_main_235"},
    {"title": "Verschenken & Tauschen", "callback_data": "category_main_272"},
]

subcategories = {
    "210": [
        {"title": "Autos", "callback_data": "category_sub_16"},
        {"title": "Autoteile & Reifen", "callback_data": "category_sub_23"},
        {"title": "Boote & Bootszubehör", "callback_data": "category_sub_11"},
        {"title": "Fahrräder & Zubehör", "callback_data": "category_sub_17"},
        {"title": "Motorräder & Motorroller", "callback_data": "category_sub_05"},
        {"title": "Motorradteile & Zubehör", "callback_data": "category_sub_06"},
        {"title": "Nutzfahrzeuge & Anhänger", "callback_data": "category_sub_76"},
        {"title": "Reparaturen & Dienstleistungen", "callback_data": "category_sub_80"},
        {"title": "Wohnwagen & -mobile", "callback_data": "category_sub_20"},
        {"title": "Weiteres Auto, Rad & Boot", "callback_data": "category_sub_41"},
    ],
    "297": [
        {"title": "Altenpflege", "callback_data": "category_sub_88"},
        {"title": "Auto, Rad & Boot", "callback_data": "category_sub_89"},
        {
            "title": "Babysitter/-in & Kinderbetreuung",
            "callback_data": "category_sub_90",
        },
        {"title": "Elektronik", "callback_data": "category_sub_93"},
        {"title": "Haus & Garten", "callback_data": "category_sub_91"},
        {"title": "Künstler/-in & Musiker/-in", "callback_data": "category_sub_92"},
        {"title": "Reise & Event", "callback_data": "category_sub_94"},
        {"title": "Tierbetreuung & Training", "callback_data": "category_sub_95"},
        {"title": "Umzug & Transport", "callback_data": "category_sub_96"},
        {"title": "Weitere Dienstleistungen", "callback_data": "category_sub_98"},
    ],
    "231": [
        {"title": "Bahn & ÖPNV", "callback_data": "category_sub_86"},
        {"title": "Comedy & Kabarett", "callback_data": "category_sub_54"},
        {"title": "Gutscheine", "callback_data": "category_sub_87"},
        {"title": "Kinder", "callback_data": "category_sub_52"},
        {"title": "Konzerte", "callback_data": "category_sub_55"},
        {"title": "Sport", "callback_data": "category_sub_57"},
        {"title": "Theater & Musical", "callback_data": "category_sub_51"},
        {
            "title": "Weitere Eintrittskarten & Tickets",
            "callback_data": "category_sub_56",
        },
    ],
    "161": [
        {"title": "Audio & Hifi", "callback_data": "category_sub_72"},
        {"title": "Dienstleistungen Elektronik", "callback_data": "category_sub_26"},
        {"title": "Foto", "callback_data": "category_sub_45"},
        {"title": "Handy & Telefon", "callback_data": "category_sub_73"},
        {"title": "Haushaltsgeräte", "callback_data": "category_sub_76"},
        {"title": "Konsolen", "callback_data": "category_sub_79"},
        {"title": "Notebooks", "callback_data": "category_sub_78"},
        {"title": "PCs", "callback_data": "category_sub_28"},
        {"title": "PC-Zubehör & Software", "callback_data": "category_sub_25"},
        {"title": "Tablets & Reader", "callback_data": "category_sub_85"},
        {"title": "TV & Video", "callback_data": "category_sub_75"},
        {"title": "Videospiele", "callback_data": "category_sub_27"},
        {"title": "Weitere Elektronik", "callback_data": "category_sub_68"},
    ],
    "17": [
        {"title": "Altenpflege", "callback_data": "category_sub_36"},
        {"title": "Baby- & Kinderkleidung", "callback_data": "category_sub_2"},
        {"title": "Baby- & Kinderschuhe", "callback_data": "category_sub_9"},
        {"title": "Baby-Ausstattung", "callback_data": "category_sub_58"},
        {"title": "Babyschalen & Kindersitze", "callback_data": "category_sub_1"},
        {
            "title": "Babysitter/-in & Kinderbetreuung",
            "callback_data": "category_sub_37",
        },
        {"title": "Kinderwagen & Buggys", "callback_data": "category_sub_5"},
        {"title": "Kinderzimmermöbel", "callback_data": "category_sub_0"},
        {"title": "Spielzeug", "callback_data": "category_sub_3"},
        {"title": "Weiteres Familie, Kind & Baby", "callback_data": "category_sub_8"},
    ],
    "185": [
        {"title": "Esoterik & Spirituelles", "callback_data": "category_sub_32"},
        {"title": "Essen & Trinken", "callback_data": "category_sub_48"},
        {"title": "Freizeitaktivitäten", "callback_data": "category_sub_87"},
        {
            "title": "Handarbeit, Basteln & Kunsthandwerk",
            "callback_data": "category_sub_82",
        },
        {"title": "Kunst & Antiquitäten", "callback_data": "category_sub_40"},
        {"title": "Künstler/-in & Musiker/-in", "callback_data": "category_sub_91"},
        {"title": "Modellbau", "callback_data": "category_sub_49"},
        {"title": "Reise & Eventservices", "callback_data": "category_sub_33"},
        {"title": "Sammeln", "callback_data": "category_sub_34"},
        {"title": "Sport & Camping", "callback_data": "category_sub_30"},
        {"title": "Trödel", "callback_data": "category_sub_50"},
        {"title": "Verloren & Gefunden", "callback_data": "category_sub_89"},
        {
            "title": "Weiteres Freizeit, Hobby & Nachbarschaft",
            "callback_data": "category_sub_42",
        },
    ],
    "80": [
        {"title": "Badezimmer", "callback_data": "category_sub_1"},
        {"title": "Büro", "callback_data": "category_sub_3"},
        {"title": "Dekoration", "callback_data": "category_sub_46"},
        {"title": "Dienstleistungen Haus & Garten", "callback_data": "category_sub_39"},
        {"title": "Gartenzubehör & Pflanzen", "callback_data": "category_sub_9"},
        {"title": "Heimtextilien", "callback_data": "category_sub_0"},
        {"title": "Heimwerken", "callback_data": "category_sub_4"},
        {"title": "Küche & Esszimmer", "callback_data": "category_sub_6"},
        {"title": "Lampen & Licht", "callback_data": "category_sub_2"},
        {"title": "Schlafzimmer", "callback_data": "category_sub_1"},
        {"title": "Wohnzimmer", "callback_data": "category_sub_8"},
        {"title": "Weiteres Haus & Garten", "callback_data": "category_sub_7"},
    ],
    "130": [
        {"title": "Fische", "callback_data": "category_sub_38"},
        {"title": "Hunde", "callback_data": "category_sub_34"},
        {"title": "Katzen", "callback_data": "category_sub_36"},
        {"title": "Kleintiere", "callback_data": "category_sub_32"},
        {"title": "Nutztiere", "callback_data": "category_sub_35"},
        {"title": "Pferde", "callback_data": "category_sub_39"},
        {"title": "Tierbetreuung & Training", "callback_data": "category_sub_33"},
        {"title": "Vermisste Tiere", "callback_data": "category_sub_83"},
        {"title": "Vögel", "callback_data": "category_sub_43"},
        {"title": "Zubehör", "callback_data": "category_sub_13"},
    ],
    "195": [
        {"title": "Auf Zeit & WG", "callback_data": "category_sub_99"},
        {"title": "Eigentumswohnungen", "callback_data": "category_sub_96"},
        {"title": "Ferien- & Auslandsimmobilien", "callback_data": "category_sub_75"},
        {"title": "Garagen & Stellplätze", "callback_data": "category_sub_97"},
        {"title": "Gewerbeimmobilien", "callback_data": "category_sub_77"},
        {"title": "Grundstücke & Gärten", "callback_data": "category_sub_07"},
        {"title": "Häuser zum Kauf", "callback_data": "category_sub_08"},
        {"title": "Häuser zur Miete", "callback_data": "category_sub_05"},
        {"title": "Mietwohnungen", "callback_data": "category_sub_03"},
        {"title": "Umzug & Transport", "callback_data": "category_sub_38"},
        {"title": "Weitere Immobilien", "callback_data": "category_sub_98"},
    ],
    "102": [
        {"title": "Ausbildung", "callback_data": "category_sub_18"},
        {"title": "Bau, Handwerk & Produktion", "callback_data": "category_sub_11"},
        {"title": "Büroarbeit & Verwaltung", "callback_data": "category_sub_14"},
        {"title": "Gastronomie & Tourismus", "callback_data": "category_sub_10"},
        {"title": "Kundenservice & Call Center", "callback_data": "category_sub_05"},
        {"title": "Mini- & Nebenjobs", "callback_data": "category_sub_07"},
        {"title": "Praktika", "callback_data": "category_sub_25"},
        {"title": "Sozialer Sektor & Pflege", "callback_data": "category_sub_23"},
        {"title": "Transport, Logistik & Verkehr", "callback_data": "category_sub_47"},
        {"title": "Vertrieb, Einkauf & Verkauf", "callback_data": "category_sub_17"},
        {"title": "Weitere Jobs", "callback_data": "category_sub_09"},
    ],
    "153": [
        {"title": "Beauty & Gesundheit", "callback_data": "category_sub_24"},
        {"title": "Damenbekleidung", "callback_data": "category_sub_54"},
        {"title": "Damenschuhe", "callback_data": "category_sub_59"},
        {"title": "Herrenbekleidung", "callback_data": "category_sub_60"},
        {"title": "Herrenschuhe", "callback_data": "category_sub_58"},
        {"title": "Taschen & Accessoires", "callback_data": "category_sub_56"},
        {"title": "Uhren & Schmuck", "callback_data": "category_sub_57"},
        {"title": "Weiteres Mode & Beauty", "callback_data": "category_sub_55"},
    ],
    "73": [
        {"title": "Bücher & Zeitschriften", "callback_data": "category_sub_6"},
        {"title": "Büro & Schreibwaren", "callback_data": "category_sub_81"},
        {"title": "Comics", "callback_data": "category_sub_84"},
        {"title": "Fachbücher, Schule & Studium", "callback_data": "category_sub_7"},
        {"title": "Film & DVD", "callback_data": "category_sub_9"},
        {"title": "Musik & CDs", "callback_data": "category_sub_8"},
        {"title": "Musikinstrumente", "callback_data": "category_sub_4"},
        {"title": "Weitere Musik, Filme & Bücher", "callback_data": "category_sub_5"},
    ],
    "400": [{"title": "Nachbarschaftshilfe", "callback_data": "category_sub_01"}],
    "235": [
        {"title": "Beauty & Gesundheit", "callback_data": "category_sub_69"},
        {"title": "Computerkurse", "callback_data": "category_sub_60"},
        {"title": "Esoterik & Spirituelles", "callback_data": "category_sub_65"},
        {"title": "Kochen & Backen", "callback_data": "category_sub_63"},
        {"title": "Kunst & Gestaltung", "callback_data": "category_sub_64"},
        {"title": "Musik & Gesang", "callback_data": "category_sub_62"},
        {"title": "Nachhilfe", "callback_data": "category_sub_68"},
        {"title": "Sportkurse", "callback_data": "category_sub_61"},
        {"title": "Sprachkurse", "callback_data": "category_sub_71"},
        {"title": "Tanzkurse", "callback_data": "category_sub_67"},
        {"title": "Weiterbildung", "callback_data": "category_sub_66"},
        {"title": "Weitere Unterricht & Kurse", "callback_data": "category_sub_70"},
    ],
    "272": [
        {"title": "Tauschen", "callback_data": "category_sub_73"},
        {"title": "Verleihen", "callback_data": "category_sub_74"},
        {"title": "Verschenken", "callback_data": "category_sub_92"},
    ],
}


# Konfigurieren Sie das Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# Funktion, die im separaten Prozess ausgeführt wird
def run_script_in_process(script_path, args):
    arg_list = ["python", script_path] + args
    subprocess.run(arg_list)


def run_async_monitor(app):
    # Create a new event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the coroutine in the event loop
    loop.run_until_complete(monitor_queue_and_notify(app))
    loop.close()


async def monitor_queue_and_notify(app):
    while True:
        (
            searchterm,
            item,
        ) = message_bus_queue.get()  # Blockiert, bis ein Element verfügbar ist
        for chat_id in chat_ids_for_notifications:
            try:
                # Erstellen Sie eine formatierte Nachricht
                message_text = (
                    f'Suche nach "{searchterm}":\n'
                    f"{item['title']}\n"
                    f"Preis: {item['price']} | {item['location']}\n"
                    f"{item['shipping']}\n"
                    f"Link: https://www.kleinanzeigen.de{item['link']}"
                )

                await app.bot.send_message(chat_id, message_text)
            except Exception as e:
                logging.error(f"Fehler beim Senden der Nachricht: {e}")


async def start_worker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Wonach möchtest du suchen?")
    return SEARCH_TERM


async def search_term(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    context.user_data["search_term"] = user_input.replace(" ", "-")
    await update.message.reply_text("In welcher Kategorie möchtest du suchen?")
    return SEARCH_CATEGORY


async def search_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    context.user_data["search_category"] = user_input
    await update.message.reply_text("Wie hoch soll der Mindestpreis sein (in Euro)?")
    return SEARCH_PRICE_MIN


async def search_price_min(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    try:
        context.user_data["search_price_min"] = int(user_input)
    except ValueError:
        await update.message.reply_text("Bitte gib eine gültige Zahl ein.")
        return SEARCH_PRICE_MIN

    await update.message.reply_text("Wie hoch soll der Maximalpreis sein (in Euro)?")
    return SEARCH_PRICE_MAX


async def search_price_max(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    try:
        context.user_data["search_price_max"] = int(user_input)
    except ValueError:
        await update.message.reply_text("Bitte gib eine gültige Zahl ein.")
        return SEARCH_PRICE_MAX

    await update.message.reply_text(
        "In welchem Intervall möchtest du suchen (in Sekunden)?"
    )
    return SEARCH_SLEEP_TIME


async def sleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    # Speichern Sie die Schlafzeit als Integer im context.user_data
    try:
        context.user_data["sleep_time"] = int(user_input)
    except ValueError:
        await update.message.reply_text("Bitte gib eine gültige Zahl ein.")
        return SEARCH_SLEEP_TIME

    chat_id = update.effective_chat.id
    chat_ids_for_notifications.add(chat_id)

    # Erstellen des Process-Objekts mithilfe der create_worker_process-Funktion
    # Hier verwenden Sie die Werte aus context.user_data
    process, worker_info = create_worker_process(
        context.user_data["search_term"],
        context.user_data["sleep_time"],
        context.user_data["search_category"],
        context.user_data["search_price_min"],
        context.user_data["search_price_max"],
    )
    process.start()  # Starten Sie den Worker-Prozess
    worker_processes.append(worker_info)

    await update.message.reply_text(
        f"Worker ({worker_info['worker_id']}) gestartet mit den Einstellungen:\n"
        f"Suchbegriff: {worker_info['search_term']}\n"
        f"Kategorie: {worker_info['search_category']}\n"
        f"Preisspanne: {worker_info['search_price_min']}€ - {worker_info['search_price_max']}€\n"
        f"Suchintervall: {worker_info['sleep_time']} Sekunden\n"
    )
    return ConversationHandler.END


# Funktion zur Erstellung eines Workers und eines Prozesses
def create_worker_process(
    search_term, sleep_time, search_category, search_price_min, search_price_max
):
    global current_worker_id

    # Create the worker process
    worker_process = multiprocessing.Process(
        target=kleinanzeigenbot.KleinanzeigenBot,
        args=(
            search_term,
            sleep_time,
            message_bus_queue,
            search_category,
            search_price_min,
            search_price_max,
        ),
    )

    # Create the worker info dictionary
    worker_info = {
        "process": worker_process,
        "search_term": search_term,
        "sleep_time": sleep_time,
        "search_category": search_category,
        "search_price_min": search_price_min,
        "search_price_max": search_price_max,
        "start_time": datetime.datetime.now(),
        "worker_id": current_worker_id,
    }

    current_worker_id += 1

    return worker_process, worker_info


async def stop_worker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if worker_processes:
        keyboard = []
        for worker_info in worker_processes:
            # Jede Zeile in der Tastatur ist eine Liste von InlineKeyboardButtons
            button_text = f"Worker ({worker_info['worker_id']})"
            callback_data = f"stop_{worker_info['worker_id']}"
            keyboard.append(
                [InlineKeyboardButton(button_text, callback_data=callback_data)]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Wähle einen Worker zum Stoppen:", reply_markup=reply_markup
        )

    else:
        await update.message.reply_text("Es gibt derzeit keine aktiven Worker.")


async def list_worker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not worker_processes:
        await update.message.reply_text("Es gibt derzeit keine aktiven Worker.")
        return

    worker_info_str = "Aktive Worker:\n\n"
    for i, worker_info in enumerate(worker_processes, start=1):
        search_term = worker_info["search_term"]
        sleep_time = worker_info["sleep_time"]
        start_time = worker_info["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        worker_id = worker_info["worker_id"]  # Holen Sie die aufsteigende Worker-ID
        worker_info_str += f"Worker (ID: {worker_id}):\n- Suchbegriff: {search_term}\n- Sleep Time: {sleep_time} Sekunden\n- Startzeit: {start_time}\n\n"

    await update.message.reply_text(worker_info_str)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Erstellen der Inline-Tasten
    keyboard = [
        [
            InlineKeyboardButton("Help-Option 1", callback_data="help_option_1"),
            InlineKeyboardButton("Help-Option 2", callback_data="help_option_2"),
        ],
        [InlineKeyboardButton("Help-Option 3", callback_data="help_option_3")],
    ]

    # Erstellen der Markup
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Senden der Nachricht mit der Markup
    await update.message.reply_text(
        "Wähle eine Option aus der Liste unten:", reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    # Überprüfen, ob die callback_data mit 'stop_' beginnt
    if data.startswith("stop_"):
        worker_id_to_stop = int(data.split("_")[1])
        for worker_info in worker_processes:
            if worker_info["worker_id"] == worker_id_to_stop:
                worker_info["process"].terminate()
                worker_processes.remove(worker_info)  # Remove from the list
                await query.edit_message_text(f"Worker {worker_id_to_stop} gestoppt.")
                return
        await query.edit_message_text(
            f"Kein Worker mit der ID {worker_id_to_stop} gefunden."
        )

    if data.startswith("category_sub_"):
        # Verarbeiten der Auswahl einer Unterkategorie
        selected_subcategory = data.split("_")[2]
        # Sie können hier eine Aktion basierend auf der ausgewählten Unterkategorie ausführen
        await query.edit_message_text(text=f"Du hast die Unterkategorie mit dem Code {selected_subcategory} gewählt!")
            
    if data.startswith("category_main_"):
        main_category_code = data.split("_")[2]
        if main_category_code in subcategories:
            keyboard = [
                [InlineKeyboardButton(sub["title"], callback_data=sub["callback_data"])]
                for sub in subcategories[main_category_code]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "Bitte wähle eine Unterkategorie:", reply_markup=reply_markup
            )
        else:
            await query.edit_message_text("Hauptkategorie nicht gefunden.")

    if data.startswith("help_"):
        # Callback-Daten verarbeiten und eine Antwort senden
        if query.data == "help_option_1":
            await query.edit_message_text(text="Du hast Option 1 gewählt!")
        elif query.data == "help_option_2":
            await query.edit_message_text(text="Du hast Option 2 gewählt!")
        elif query.data == "help_option_3":
            await query.edit_message_text(text="Du hast Option 3 gewählt!")

def main():
    # Erstellen Sie den Updater und übergeben Sie Ihr Bot-Token.
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Starten Sie den Überwachungsthread
    threading.Thread(target=run_async_monitor, args=(app,), daemon=True).start()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("startworker", start_worker)],
        states={
            SEARCH_TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_term)],
            SEARCH_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_category)
            ],
            SEARCH_PRICE_MIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_price_min)
            ],
            SEARCH_PRICE_MAX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_price_max)
            ],
            SEARCH_SLEEP_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sleep_time)
            ],
        },
        fallbacks=[],
    )

    # Definieren Sie CommandHandler
    app.add_handler(CommandHandler("stopworker", stop_worker))
    app.add_handler(CommandHandler("listworker", list_worker))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.add_handler(CommandHandler("categories", show_main_categories))

    # Starten Sie den Bot
    app.run_polling()


if __name__ == "__main__":
    main()
