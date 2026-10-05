"""
Configuration file for the project.
Manages settings and parameters for the application.
"""
import json
import os
import time
# from web_utils import print_style

# Run browser in headless mode (True or False). Headless mode is invisible and runs in the background. Set to False to see the browser window.
# Headless mode is useful for automated testing and running scripts without user interaction, is also faster and consumes less resources,
# while non-headless mode allows you to see the browser actions in real-time.
HEADLESS = False

BROWSER_SLOW = 1500  # Timeout for browser operations in milliseconds

SKIP_CONFIG_MENU = True

SETTINGS_FILE = "settings_cv.json"

BRAVE_PATHS_WINDOWS = [
    "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
    "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
]
MODE_LABELS = {
    True: "Hidden (Fast)",
    False: "Visible (Watch it work)"
}


def load_settings():
    """Checking for a settings file and reads."""
    if os.path.exists(SETTINGS_FILE):
        if os.path.getsize(SETTINGS_FILE) == 0:
            print(
                f"Hi Hi! Looks like {SETTINGS_FILE} isn't set up properly. Let's set up your browser preferences!\n")
            return {}
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                loaded_settings = json.load(file)
                if not loaded_settings:
                    return {}

                return loaded_settings
        except json.JSONDecodeError:
            print(
                f"⚠️ Error: {SETTINGS_FILE} is not a valid JSON file. Perhaps it is empty or corrupted. Please check the file.")
            return {}
        except Exception as e:
            print(f"⚠️ Error loading settings: {e}")
            return {}
    return {}


def save_settings(settings_data):
    """Adding preferences to the settings file."""
    # Loading existing settings if the file exists
    existing_settings = load_settings()

    # Merge the existing settings with the new ones
    existing_settings.update(settings_data)

    with open(SETTINGS_FILE, 'w', encoding="utf-8") as file:
        json.dump(existing_settings, file, indent=4)


def get_brave_path():
    """Returns the path to the Brave browser executable, if possible."""
    for path in BRAVE_PATHS_WINDOWS:
        if os.path.exists(path):
            return path
    return None


def prompt_display_mode():
    """
    Prompts the user to select a display mode (headless or non-headless).
    """

    print(
        "🤖 Please select a browser mode: \n\x1b[3m(Can be changed later)\x1b[0m\n")
    print("1.) Headless (Invisible) - runs in the background without opening a browser window")
    print("2.) Non-Headless (Visible) - opens a browser window and shows the actions being performed")
    print("\n Press 3 to exit the program.")

    print("\n \x1b[3mNote: Headless mode is faster and consumes less resources, "
          "while Non-Headless mode allows you to see the browser actions in real-time."
          " If you're not sure, I recommend starting with Headless mode!♥\x1b[0m\n")

    mode_choice = input("What would you like to use? (1 or 2): ").strip()

    if mode_choice == "3":
        print("🤖 Exiting the program. Goodbye! ♥")
        exit()
    elif mode_choice not in ["1", "2"]:
        print("⚠️ Invalid! Defaulting to Headless mode. You can change this later in the settings.\n")
        mode_choice = "1"

    is_headless = True if mode_choice == "1" else False
    print(f"\n 🤖 You selected {MODE_LABELS[is_headless]}!\n")
    return is_headless


def prompt_browser_choice():
    """
    Prompts the user to select a browser.
    Returns the path to the selected browser or an empty string for Playwright's default browser.
    """
    print("\n🤖 Time to set up your browser preferences! \n")
    print("Please select the browser you want to use for this program:\n")
    print("1.) Brave Browser (Recommended)\n")
    print("2.) Playwright's default browser (Chromium)\n")
    print("Press 3 to exit the program.\n")

    browser_choice = input(
        "Which browser would you like to use? (1, 2, or 3): ").strip()

    if browser_choice == "1":
        brave_path = get_brave_path()
        if brave_path:
            print(f"\n🤖 Brave browser found at: {brave_path}\n")
            return brave_path
        else:
            print(
                "\n⚠️ Brave browser not found. Please install Brave or select another browser.\n")
            exit()
    elif browser_choice == "2":
        return ""  # Playwright will use its default browser
    elif browser_choice == "3":
        print("🤖 Exiting the program. Goodbye! ♥")
        exit()
    else:
        print("⚠️ Please enter 1, 2, or 3.")


def config_browser():
    """
    Configures the browser settings by prompting the user for their preferences and saving them to a settings file.
    """
    # Load existing settings if available
    settings = load_settings()

    # Check if the browser path is already saved in settings
    if "browser_path" in settings and "is_headless" in settings:
        browser_path = settings["browser_path"]
        is_headless = settings["is_headless"]

        # Display the loaded settings to the user
        print(f"🤖 Loaded saved browser path: {browser_path}\n")
        time.sleep(1)
        print(f"🤖 Loaded saved browser setting: {MODE_LABELS[is_headless]}\n")
        time.sleep(1)

        return is_headless, browser_path

    # Setting up the browser preferences for the first time
    print("\nHi Hi! Looks like your browser settings aren't set up yet! "
          "Let's configure your browser!\n")
    is_headless = prompt_display_mode()
    browser_path = prompt_browser_choice()

    # 3. Save choices!
    save_settings({"is_headless": is_headless, "browser_path": browser_path})

    print("\n✅ Setting saved!\n")
    time.sleep(1.5)

    return is_headless, browser_path


class ExcelColumns:
    """Variables for all the Column Labels to use in the main code"""
    CLIENT = "Client Name"
    INSTITUTION = "Institution"
    LOCATION = "Location"
    LIC_NAME = "License Name"
    ON_NURSYS = "On NURSYS?"
    LIC_ID = "License ID"
    LIC_TYPE = "License Type"
    LIC_STATUS = "License Status"
    VERIF_STATUS = "Verification Status"
    ISSUE_DATE = "License Original Issue Date"
    ACCREDITED = "Accredited Since"
    EXP_DATE = "License Expiration Date"
    REVIEW_DATE = "Next Review Date"
    DATE_VERIFIED = "Date Verified"
    COMPACT = "Compact Status"
    DATABASES = "Databases Used"
