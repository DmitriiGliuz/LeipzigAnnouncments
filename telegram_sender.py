import os

import requests

from config_handlers import load_config
from messages_builder import messages_generator
from logger import logger


def send_message(message, channel_id):
    """
    Sends a message to a Telegram channel
    :param message:
    :param channel_id:
    :return:
    """
    logger.info(f"Sending message to channel {channel_id}")
    config = load_config()
    bot_token = config['bot_token']
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    data = {
        'chat_id': channel_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print('Message sent successfully!\n')
        logger.info("Message sent successfully")
    else:
        logger.error(f"Failed to send message. Error code: {response.status_code}")


def parse_websites_and_send_messages(channel_id: str):
    """
    Parses websites and sends messages to a Telegram channel
    :param channel_id:
    :return:
    """
    dates_and_messages = messages_generator()
    for date, message_text in dates_and_messages:
        print(date)
        logger.info(f"Sending message for {date}")
        send_message(message_text, channel_id)


def send_messages_from_files(channel_id: str):
    """
    Sends messages from files to a Telegram channel
    :param channel_id:
    :return:
    """
    for file_name in os.listdir("tg_messages"):
        print(file_name)
        logger.info(f"Sending message from file {file_name}")
        with open(f"tg_messages/{file_name}", 'r', encoding='utf-8') as f:
            send_message(f.read(), channel_id)
