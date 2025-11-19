# Kleinanzeigen Telegram Bot

## Overview
This Telegram Bot monitors the Kleinanzeigen website for new listings that match user-defined search terms and time intervals. The bot utilizes the Telegram API to notify users immediately when new offers are found.

## How It Works
- **Monitoring**: The bot continuously scans Kleinanzeigen for specific search keywords.
- **Notifications**: Users receive automatic updates via Telegram whenever a new listing is found.
- **Customization**: Users can define search terms and polling intervals according to their preferences.

## Setup
1. **Prerequisites**:
   - Python 3.6 or newer
   - Required libraries: `telegram`, `beautifulsoup4`, `multiprocessing`, `threading`, `asyncio`.

2. **Bot Token**:
   - Create a new bot via [BotFather](https://t.me/botfather) on Telegram and copy the Bot Token.

3. **Configuration**:
   - Replace `BOT_TOKEN` in the main file with your personal Bot Token.

4. **Install Dependencies**:
   - Run `pip install -r requirements.txt` to install the necessary libraries.

## Usage
- **Start Bot**: Run `python telegram_bot.py`.
- **Start Worker**: Send `/startworker` in the chat to begin monitoring.
- **Set Search Term**: Follow the instructions in the chat to define search terms and intervals.
- **Stop Worker**: Send `/stopworker` to stop monitoring.
- **List Workers**: Send `/listworker` to view active monitoring tasks.

## Advanced Features
- **Error Handling**: The bot includes a reliable error handling system.
- **Logging**: Comprehensive logging capabilities assist with troubleshooting and debugging.

## License
This project is licensed under the MIT License. It is free for both private and commercial use.

## Contributing
Improvements and suggestions are always welcome. Please submit pull requests or report issues in the GitHub repository.

## Disclaimer
This bot is not affiliated with the official Kleinanzeigen website and is intended for educational purposes only.
