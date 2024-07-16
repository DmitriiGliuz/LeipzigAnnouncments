import json
import re
from datetime import datetime

from logger import logger

CONFIG_FILE_PATH = "config.json"


class InvalidConfigError(Exception):
    def __init__(self, message):
        super().__init__(message)
        logger.error(message)


def validate_bot_token(token: str):
    """
    Validates the bot token format
    :param token:
    :return:
    """
    logger.info(f"Validating bot token")
    if not re.match(r"\d+:.*", token):
        raise InvalidConfigError("Wrong bot token format")
    logger.info(f"Bot token is valid")


def validate_channel_id(channel_id: str):
    """
    Validates the channel ID format
    :param channel_id:
    :return:
    """
    logger.info(f"Validating channel ID")
    if not re.match(r"-\d+", channel_id):
        raise InvalidConfigError("Wrong channel ID format")
    logger.info(f"Channel ID is valid")


def validate_date(date: str):
    """
    Validates the date format
    :param date:
    :return:
    """
    try:
        logger.info(f"Validating date format")
        if not re.fullmatch(r"""\d{4}-\d{2}-\d{2}""", date):
            raise ValueError()
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise InvalidConfigError("Wrong date format. The start date should have YYYY-MM-DD format")
    logger.info(f"Date format is valid")


def validate_days_limit(days_limit):
    """
    Validates the days limit format
    :param days_limit:
    :return:
    """
    logger.info(f"Validating days limit")
    error_message = "Days limit value should be a positive integer number"
    if isinstance(days_limit, str):
        if not re.fullmatch(r"\d+", days_limit):
            raise InvalidConfigError(error_message)
        else:
            days_limit = int(days_limit)
    if days_limit < 1:
        raise InvalidConfigError(error_message)
    logger.info(f"Days limit is valid")


def validate_config_format(config: dict):
    """
    Validates the configuration file format
    :param config:
    :return:
    """
    expected_keys_and_types = {
        "bot_token": str,
        "channel_id": str,
        "testing_channel_id": str,
        "start_date": str,
        "move_start_date_week_forward_after_parsing": bool,
        "days_limit": int
    }

    for expected_key, expected_type in expected_keys_and_types.items():
        logger.info(f"Validating key {expected_key}")
        if expected_key not in config:
            raise InvalidConfigError(f"Key {expected_key} is missing in configuration file")
        if not isinstance(config[expected_key], expected_type):
            raise InvalidConfigError(f"Value for {expected_key} should be {expected_type}")

    validate_bot_token(config["bot_token"])
    validate_channel_id(config["channel_id"])
    validate_channel_id(config["testing_channel_id"])
    validate_date(config["start_date"])
    validate_days_limit(config["days_limit"])
    logger.info(f"Configuration file format is valid")


def load_config():
    """
    Loads the configuration file
    :return:
    """
    logger.info(f"Loading configuration file")
    try:
        with open(CONFIG_FILE_PATH, 'r') as json_file:
            config = json.load(json_file)
            validate_config_format(config)
            return config
    except FileNotFoundError:
        raise InvalidConfigError("Configuration file not found")


def save_config(config: dict):
    """
    Saves the configuration file
    :param config:
    :return:
    """
    logger.info(f"Saving configuration file")
    validate_config_format(config)
    try:
        with open(CONFIG_FILE_PATH, 'w') as json_file:
            json.dump(config, json_file, indent=4)
    except FileNotFoundError:
        raise InvalidConfigError("Configuration file not found")


def set_config_property(_property: str, _value):
    """
    Sets the configuration property
    :param _property:
    :param _value:
    :return:
    """
    config = load_config()
    logging.info(f"Setting property {_property} to {_value}")
    config[_property] = _value
    save_config(config)
