"""
Configuration file for the project.
Manages settings and parameters for the application.
"""
import json
import os
import time
from web_utils import print_style

# Run browser in headless mode (True or False). Headless mode is invisible and runs in the background. Set to False to see the browser window.
# Headless mode is useful for automated testing and running scripts without user interaction, is also faster and consumes less resources,
# while non-headless mode allows you to see the browser actions in real-time.
HEADLESS = False

BROWSER_SLOW = 1500  # Timeout for browser operations in milliseconds

SKIP_CONFIG_MENU = True

SETTINGS_FILE = "settings_cv.json"


def load_settings():
    """Checking for a settings file and reads."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as file:
            return json.load(file)
    return None


def save_settings(settings_data):
    """Adding preferences to the settings file."""
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(settings_data, file, indent=4)


def config_browser():
    """
    Asks the user to select a browser and whether to run in headless mode.
    """

    settings = load_settings()

    if settings and "is_headless" in settings:
        is_headless = settings["is_headless"]

        mode = "Hidden (Fast)" if is_headless else "Visible (Watch it work)"
        print(f"🤖 Loaded saved browser setting: {mode}\n")
        time.sleep(1)
        return is_headless

    print(
        "\nHi Hi!\n\nPlease select a browser mode: \n\x1b[3m(Can be changed later)\x1b[0m\n")
    print("1.) Headless (Invisible) - runs in the background without opening a browser window")
    print("2.) Non-Headless (Visible) - opens a browser window and shows the actions being performed")
    print("\n Press 3 to exit the program.")

    print("\n \x1b[3mNote: Headless mode is faster and consumes less resources, "
          "while Non-Headless mode allows you to see the browser actions in real-time."
          " If you're not sure, I recommend starting with Headless mode!♥\x1b[0m\n")
    choice = input("What would you like to use? (1 or 2): ").strip()

    is_headless = True if choice == "1" else False

    # 3. Save choice!
    save_settings({"is_headless": is_headless})

    print("\n✅ Setting saved! I won't ask you again.\n")
    time.sleep(1.5)

    return is_headless
