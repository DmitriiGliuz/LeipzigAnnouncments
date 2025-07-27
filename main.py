import os

from config_handlers import load_config, set_config_property, InvalidConfigError
from date_handlers import move_start_date_in_config_week_forward, set_start_date_to_closest_monday
from telegram_messages_builder import create_files
from telegram_sender import send_messages_from_files, parse_websites_and_send_messages

config_is_valid = False
try:
    config = load_config()
    MAIN_CHANNEL_ID = config['channel_id']
    TESTING_CHANNEL_ID = config['testing_channel_id']
    config_is_valid = True
except InvalidConfigError as e:
    print(f"Error in configuration file: {e}")
except FileNotFoundError:
    print("Error: Configuration file not found")

HORIZONTAL_LINE = '_' * 50


def run_after_confirm_screen(message: str, func, *args, show_starting=True):
    if message[0].isupper():
        original_letter = message[0]
        lowercase_letter = original_letter.lower()
        message = message.replace(original_letter, lowercase_letter, 1)
    user_input = input(f"Press Y if you want to {message}: ")
    if user_input.lower() == 'y':
        if show_starting:
            print("Starting...")
        func(*args)
        print("Done!\n")
    else:
        print("Ok, the action is cancelled.")


def update_config():
    config.update(load_config())


def print_config():
    update_config()
    print(f"""Current configuration:
    Start date: {config["start_date"]}
    Move start date property a week_forward after parsing: {config["move_start_date_week_forward_after_parsing"]}
    Days limit: {config["days_limit"]}""")


def print_caption(caption: str):
    print(caption)
    print(HORIZONTAL_LINE)


def print_caption_and_config(caption: str):
    print_caption(caption)
    print_config()
    print(HORIZONTAL_LINE)


def print_error(message: str):
    print(f"Error: {message}. Try again.")


def choose_item_screen(actions: tuple, caption="Available actions:", prompt="Enter your choice: ") -> str:
    print(f"\n{caption}")
    for index, action in enumerate(actions):
        print(f"{index + 1}. {action}")
    while True:
        user_choice = input(prompt)
        if not user_choice.isdigit():
            print_error("Your input is not an integer number")
        else:
            user_choice = int(user_choice)
            last_point_number = len(actions)
            if user_choice not in range(1, last_point_number + 1):
                print_error(f"Your input must be a number from 1 to {last_point_number}")
            else:
                print()
                return actions[user_choice - 1]


# Menu items for configuration editing screen
START_DATE = "Edit start date"
SET_START_DATE_TO_CLOSEST_MONDAY = "Set start date to closest monday"
MANUALLY_MOVE_START_DATE = "Manually move the start date a week forward"
MOVE_START_DATE = "Move the start date a week forward after parsing"
DAYS_LIMIT = "Edit days limit"
BACK = "Go back"
ON = "On"
OFF = "Off"


def change_setting(message, _property: str, value):
    run_after_confirm_screen(message, set_config_property, _property, value, show_starting=False)
    update_config()


def change_boolean_config_property_screen(caption: str, _property):
    print_caption(f"Edit: {caption}")
    available_options = (ON, OFF, BACK)
    chosen_option = choose_item_screen(available_options, "Available options:")
    if chosen_option == ON:
        change_setting(f"turn on: {caption}", _property, True)
    elif chosen_option == OFF:
        change_setting(f"turn off: {caption}", _property, False)
    else:
        return


def edit_start_date_screen():
    while True:
        user_input = input("Input the new start date in YYYY-MM-DD format or press Enter to go back: ").strip()
        if not user_input:
            return
        try:
            change_setting(f"change start date to {user_input}", "start_date", user_input)
            return
        except InvalidConfigError as config_error:
            print_error(str(config_error))


def edit_days_limit_screen():
    while True:
        user_input = input("Input the new days limit format or press Enter to go back: ").strip()
        if not user_input:
            return
        try:
            change_setting(f"change days limit to {user_input}", "days_limit", int(user_input))
            return
        except InvalidConfigError as config_error:
            print_error(str(config_error))


def edit_config_screen():
    while True:
        print_caption_and_config("Editing configuration")
        config_items = (
            START_DATE, SET_START_DATE_TO_CLOSEST_MONDAY, MANUALLY_MOVE_START_DATE, MOVE_START_DATE, DAYS_LIMIT, BACK)
        item_to_edit = choose_item_screen(config_items)
        if item_to_edit == START_DATE:
            edit_start_date_screen()
        elif item_to_edit == SET_START_DATE_TO_CLOSEST_MONDAY:
            run_after_confirm_screen(SET_START_DATE_TO_CLOSEST_MONDAY, set_start_date_to_closest_monday,
                                     show_starting=False)
        elif item_to_edit == MANUALLY_MOVE_START_DATE:
            run_after_confirm_screen(MANUALLY_MOVE_START_DATE, move_start_date_in_config_week_forward,
                                     show_starting=False)
        elif item_to_edit == MOVE_START_DATE:
            change_boolean_config_property_screen(MOVE_START_DATE, 'move_start_date_week_forward_after_parsing')
        elif item_to_edit == DAYS_LIMIT:
            edit_days_limit_screen()
        else:
            break


def delete_all_files_with_messages():
    dir_path = "tg_messages"
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"{file_path} - deleted")


# Main menu items
PARSE_AND_SEND_TO_TESTING = "Parse websites and send messages directly to the TESTING channel"
PARSE_AND_SEND_TO_MAIN = "Parse websites and send messages directly to the MAIN channel"
CREATE_FILES = "Parse websites and create files with announcements"
POST_TO_TESTING = "Post announcements from files to the TESTING channel"
POST_TO_MAIN = "Post announcements from files to the MAIN channel"
PRINT_CONFIG = "Print configuration"
EDIT_CONFIG = "Edit configuration"
DELETE_FILES = "Delete files with texts for Telegram posts"
EXIT = "Exit"


def main_menu():
    print_caption_and_config("Leipzig Announcements Bot command line interface")
    main_menu_actions = (
        PARSE_AND_SEND_TO_TESTING, PARSE_AND_SEND_TO_MAIN, CREATE_FILES, POST_TO_TESTING, POST_TO_MAIN,
        PRINT_CONFIG, DELETE_FILES,
        EDIT_CONFIG, EXIT)

    first_run = True
    while True:
        if first_run:
            first_run = False
        else:
            print_caption("Main menu")

        main_menu_action = choose_item_screen(main_menu_actions)
        if main_menu_action == EXIT:
            break
        elif main_menu_action == PARSE_AND_SEND_TO_TESTING:
            run_after_confirm_screen(PARSE_AND_SEND_TO_TESTING, parse_websites_and_send_messages, TESTING_CHANNEL_ID)
        elif main_menu_action == PARSE_AND_SEND_TO_MAIN:
            run_after_confirm_screen(PARSE_AND_SEND_TO_MAIN, parse_websites_and_send_messages, MAIN_CHANNEL_ID)
        elif main_menu_action == CREATE_FILES:
            run_after_confirm_screen(CREATE_FILES, create_files)
        elif main_menu_action == POST_TO_TESTING:
            run_after_confirm_screen(POST_TO_TESTING, send_messages_from_files, TESTING_CHANNEL_ID)
        elif main_menu_action == POST_TO_MAIN:
            run_after_confirm_screen(POST_TO_MAIN, send_messages_from_files, MAIN_CHANNEL_ID)
            run_after_confirm_screen(DELETE_FILES, delete_all_files_with_messages)
        elif main_menu_action == PRINT_CONFIG:
            print_config()
            print()
        elif main_menu_action == DELETE_FILES:
            run_after_confirm_screen(DELETE_FILES, delete_all_files_with_messages)
        elif main_menu_action == EDIT_CONFIG:
            edit_config_screen()

if __name__ == "__main__":
    if config_is_valid:
        set_start_date_to_closest_monday()
        main_menu()
    print("Bye!")
