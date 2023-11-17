from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

import logging

import multiprocessing
import subprocess
import datetime

BOT_TOKEN = "6616611678:AAEVGAnVbc2w2biSU4JqvI9m-KA5hq_4pm8"

# Definieren Sie Konstanten für die verschiedenen Stadien der Konversation
SEARCH_TERM, SLEEP_TIME = range(2)

worker_processes = []
next_worker_id = 0


# Konfigurieren Sie das Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# Funktion, die im separaten Prozess ausgeführt wird
def run_script_in_process(script_path, args):
    arg_list = ["python", script_path] + args
    subprocess.run(arg_list)


async def start_worker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Wonach möchtest du suchen?")
    return SEARCH_TERM

async def search_term(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    context.user_data['search_term'] = user_input.replace(' ', '-')
    await update.message.reply_text("Wie oft möchtest du suchen (in Sekunden)?")
    return SLEEP_TIME

async def sleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:    
    user_input = update.message.text
    context.user_data['sleep_time'] = user_input

    # Erstellen des Process-Objekts mithilfe der create_worker_process-Funktion
    process, worker_info = create_worker_process(context.user_data['search_term'], context.user_data['sleep_time'])

    # Prozess starten
    process.start()

    # Dictionary zur Liste hinzufügen
    worker_processes.append(worker_info)

    await update.message.reply_text("Worker gestartet mit den Einstellungen:\n"
                                    f"Suchbegriff: {worker_info['search_term']}\n"
                                    f"Sleep Time: {worker_info['sleep_time']} Sekunden\n"
                                    f"Worker ID: {worker_info['worker_id']}")
    return ConversationHandler.END

# Funktion zur Erstellung eines Workers und eines Prozesses
def create_worker_process(search_term, sleep_time):

    # Verwenden Sie die nächste aufsteigende ID
    global next_worker_id
    worker_id = next_worker_id
    next_worker_id += 1


    process = multiprocessing.Process(
        target=run_script_in_process, 
        args=("kleinanzeigenbot.py", [search_term, sleep_time])
    )

    # Erstellen des Dictionary mit Metadaten, einschließlich der aufsteigenden ID
    worker_info = {
        "process": process,
        "search_term": search_term,
        "sleep_time": sleep_time,
        "start_time": datetime.datetime.now(),
        "worker_id": worker_id  # Weisen Sie dem Worker eine aufsteigende ID zu
    }

    return process, worker_info

async def stop_worker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Bitte geben Sie die ID des zu stoppenden Workers an.")
        return

    worker_id_to_stop = int(context.args[0])  # Wandeln Sie die ID in eine Ganzzahl um
    process_stopped = False

    for worker_info in worker_processes:
        if worker_info["worker_id"] == worker_id_to_stop:
            worker_info["process"].terminate()
            worker_info["process"].join(timeout=10)  # Warten Sie auf das Beenden des Prozesses für maximal 10 Sekunden
            if not worker_info["process"].is_alive():
                process_stopped = True
                break

    if process_stopped:
        await update.message.reply_text(f"Worker mit ID '{worker_id_to_stop}' erfolgreich gestoppt.")
    else:
        await update.message.reply_text(f"Kein Worker mit ID '{worker_id_to_stop}' gefunden oder konnte nicht gestoppt werden.")



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
        worker_info_str += f"Worker {worker_id}:\n- Suchbegriff: {search_term}\n- Sleep Time: {sleep_time} Sekunden\n- Startzeit: {start_time}\n\n"

    await update.message.reply_text(worker_info_str)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Displays info on how to use the bot."""

    await update.message.reply_text(

        "to be implemented..."

    )


def main():
    # Erstellen Sie den Updater und übergeben Sie Ihr Bot-Token.
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('startworker', start_worker)],
        states={
            SEARCH_TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_term)],
            SLEEP_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, sleep_time)],
        },
        fallbacks=[],
    )

    # Definieren Sie CommandHandler
    app.add_handler(CommandHandler("stopworker", stop_worker))
    app.add_handler(CommandHandler("listworker", list_worker))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(conv_handler)
        
    # Starten Sie den Bot
    app.run_polling()
    


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
