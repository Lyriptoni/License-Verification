"""
Configuration file for the project.
Manages settings and parameters for the application.
"""

# Run browser in headless mode (True or False). Headless mode is invisible and runs in the background. Set to False to see the browser window.
# Headless mode is useful for automated testing and running scripts without user interaction, is also faster and consumes less resources,
# while non-headless mode allows you to see the browser actions in real-time.
HEADLESS = False

BROWSER_SLOW = 1500  # Timeout for browser operations in milliseconds

SKIP_CONFIG_MENU = True


def config_browser():
    """
    Asks the user to select a browser and whether to run in headless mode.
    """

    global HEADLESS

    if SKIP_CONFIG_MENU:
        if HEADLESS:
            print("Default set to background browswer mode (Headless)")
        else:
            print("Default set to opens browser mode (Non-Headless)")
        return HEADLESS

    while True:
        print(
            "\nHi Hi!\n\nPlease select a browser mode: \n\x1b[3m(Can be changed later)\x1b[0m\n")
        print("1.) Headless (Invisible) - runs in the background without opening a browser window")
        print("2.) Non-Headless (Visible) - opens a browser window and shows the actions being performed")
        print("\n Press 3 to exit the program.")

        print("\n \x1b[3mNote: Headless mode is faster and consumes less resources, "
              "while Non-Headless mode allows you to see the browser actions in real-time."
              " If you're not sure, I recommend starting with Headless mode!♥\x1b[0m\n")
        choice = input("What would you like to use? (1 or 2): ").strip()

        if choice == "1":
            HEADLESS = True
            print(
                "\nHeadless mode selected. You may not see it, but I promise it's working!♥\n")
            return HEADLESS
        elif choice == "2":
            HEADLESS = False
            print(
                "\nNon-Headless mode selected. Get your popcorn ready! Let's watch some tv!♥\n")
            return HEADLESS

        elif choice == "3":
            print("\nAlrighty! Exiting now... ByeBye!♥\n")
            import sys
            sys.exit()
        else:
            print("\nThat's not a valid option. Try again?\n")
