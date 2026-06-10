"""This script reads an Excel file containing client information, processes each client's license status, and updates the Excel file with the verification results.
It checks if the client's license is active and updates the status, expiry date, and verification date accordingly."""

import os
import shutil
import pandas as pd
import config
import web_utils
from tkinter import filedialog, Tk
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()  # Load environment variables from .env file

claude_client = Anthropic(api_key=os.getenv("CLAUDE_KEY"))

# Methods:


def clear_console():
    """Clears the console for better readability."""
    os.system('cls' if os.name == 'nt' else 'clear')


def ask_claude_for_license_verification(institution, location, license_name, license_type):
    """Sends a request to Claude for license verification using public data and returns the response."""

    if not license_type or str(license_type).strip() == "":
        license_type = "N/A"

    prompt = f"""

    You are an expert medical credentials verification assistant.
    Analyze the following credential data to determine the correct registry pathway:

    Institution: {institution}
    Location: {location}
    License Name: {license_name}
    License Type: {license_type}

    RULES FOR TARGET DATABASE:
    1. CRITICAL: If the Location is clearly outside of the United States (e.g., Japan, Canada, UK, Europe, International), set TARGET DATABASE to 'International Registry' and METHOD to 'Automatic'.
    2. If the Location is in the US AND the License Type is 'N/A' or an institutional accreditation, set TARGET DATABASE to 'DAPIP' and METHOD to 'Automatic'.
    3. If the Location is in the US AND the License Type relates to Nursing (like RN, LPN), set TARGET DATABASE to 'NURSYS' and METHOD to 'Automatic'.
    4. If it is an individual medical practitioner in the US not covered above, determine the exact state board (e.g., 'Texas Medical Board') and set METHOD to 'Manual Required'.

    RULES FOR CLEANED SEARCH TERM:
    1. If TARGET DATABASE is 'DAPIP', the CLEANED SEARCH TERM must ONLY be the core name of the school or institution. Strip out trailing branch locations, cities, states, or zip codes (e.g., if input is 'Culinary Institute of America, Hyde Park, New York', return 'Culinary Institute of America').
    2. If it is an individual person, clean up their name to just 'Firstname Lastname'.

    RULES FOR VERIFICATION METHOD:
    1. Set METHOD to 'Automatic' for DAPIP and NURSYS.
    2. Set METHOD to 'Manual Required' for International Registry, or if the registry requires a paid account, individual user login credentials, or heavy security gates.

    Respond in this exact, strict format:
    TARGET DATABASE: [Name of database, state board, or official registry website]
    VERIFICATION METHOD: [Automatic OR Manual Required]
    CLEANED SEARCH TERM: [The cleaned up string based on the rules above]
    """

    response = claude_client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()


def extract_claude_response(response):
    """Turns Claude's response into structured data for
    target database and cleans up the search term."""
    lines = response.strip().split("\n")

    target_db = "Unknown Registry"
    search_term = "Unknown School Name"
    verify_method = "Unknown Method"

    for line in lines:
        if line.startswith("TARGET DATABASE:"):
            target_db = line.split(":", 1)[1].strip()
        elif line.startswith("CLEANED SEARCH TERM:"):
            search_term = line.split(":", 1)[1].strip()
        elif line.startswith("VERIFICATION METHOD:"):
            verify_method = line.split(":", 1)[1].strip()

    return target_db, search_term, verify_method


def select_excel_file():
    """Opens a file dialog for the user to select an Excel file."""
    root = Tk()
    root.withdraw()  # Hide the root window

    print("Please select the Excel file containing client license information for verification.")

    file_path = filedialog.askopenfilename(
        title="Select Excel File",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )

    if not file_path:
        print("No file selected. Exiting.")
        return None
    print(f"Selected file: {file_path}")
    return file_path


def backup_excel_file(file_path):
    """Creates a backup of the Excel file before making any changes."""
    # Creating folder for backup if it doesn't exist
    if not os.path.exists("backup"):
        os.makedirs("backup")

    # Getting the base name of the file
    base_name = os.path.basename(file_path)

    # Splitting the name and extension
    name_without_ext = os.path.splitext(base_name)[0]

    timestamp = datetime.now().strftime("%m%d%Y_%H%M%S")
    backup_file_name = f"backup/{name_without_ext}_Backup_{timestamp}.xlsx"

    if os.path.exists(file_path):
        shutil.copy(file_path, backup_file_name)
        print(f"Backup created: {backup_file_name}")


def clean_excel_data(data):
    """Cleans the Excel data by ensuring all necessary columns are present,
    filling missing values with empty strings, and standardizing data types."""

    columns_cleaned = [
        "Client Name", "Institution",
        "Location", "License Name", "Status",
        "Expiration Date", "Date Verified", "Database"
    ]

    for column_label in columns_cleaned:
        if column_label not in data.columns:
            # Add the column with a default value
            data[column_label] = ""

        else:
            # Fill missing values with empty strings
            data[column_label] = data[column_label].fillna("")
            # Force everything to be a clean string data type
            data[column_label] = data[column_label].astype(str)
            # Replace literal "nan" text strings left behind by Excel
            data[column_label] = data[column_label].replace("nan", "")
            # Cleanly shave whitespace
            data[column_label] = data[column_label].str.strip()

    return data


def welcome_banner():
    """Displays a welcome banner when the program starts."""
    banner = """
          .  . * .  .
         (            )
       (    \x1b[3mStarting\x1b[0m    )
      (   \x1b[3mVerification\x1b[0m   )
       (    \x1b[3mProcess\x1b[0m     )
         (            )
           '  ' * '  '
    """
    print(banner)


def run_license_verification(is_headless):
    """Main function to run the license verification process."""

    excel_file = select_excel_file()

    if not excel_file:
        print("No Excel file selected. Ending process. Please restart and select a file to proceed. ♥")
        return None

    backup_excel_file(excel_file)

    # Read all data as strings to avoid issues with NaN values
    raw_data = pd.read_excel(excel_file, dtype=str)
    print("\nExcel file loaded successfully.\n")
    data = clean_excel_data(raw_data)

    # Allows User to choose how to complete the task:

    print("==================================================")
    print("How Do We Want to Work Today?:")
    print("==================================================\n")
    print("1. AI Does Most of the Work (Automated Research and Verification via Claude AI)\n")
    print("2. I'll Do the Research Myself, thank you! (You do the research, Claude assist with data entry)")
    print("=======================================================================================================\n")
    mode_choice = input("Your choice is? (1 or 2):\n\n ").strip()

    # Tracking progress counters:
    count_processed = 0
    count_skipped = 0

    if mode_choice == "1":
        print("\n 🤖Calling Claude for assistance... 🤖\n")

    for i, row in data.iterrows():

        # Checking if status is not empty first.
        if str(row["Status"]).strip() != "":
            print(
                f"Row {i + 1}: {row['Client Name']}'s status is already set. Completed already? Skipping...\n")
            count_skipped += 1
            continue

        # Manual Mode
        if mode_choice == "2":
            print(
                "Rapid Fire Mode: \nHere's what we're working with: \n")
            print(f"Row {i+1}: Data Entry for {row['Client Name']}!\n")
            print(
                f"Instituion: {row['Institution']} | {row['Location']} | License ID: {row['License ID']}")
            print(
                "===========================================================================================\n")
            print(
                "We're looking for the expiration date... Or, press Enter to skip this row!:\n")
            user_date_entered = input("Enter the Expiration Date:\n ")

            if user_date_entered.lower() in ["exit", "q"]:
                print(f"Exit requested, saving progress at row {i}")
                count_processed -= 1
                break

            current_time = datetime.now().strftime("%m-%d-%Y @ %I:%M%p")
            data.at[i, 'Status'] = "Manually Processed"
            data.at[i, 'Expiration Date'] = web_utils.date_correcter(
                user_date_entered)
            data.at[i, 'Date Verified'] = str(current_time)
            data.at[i, 'Database'] = "Manual Entry Deck"
            count_processed += 1
            continue

        # Automated Mode
        print(f"Processing new Client: {row['Client Name']}")
        count_processed += 1

        lisc_institute = row['Institution']
        lisc_location = row['Location']
        lisc_name = row['License Name']
        lisc_id = row['License ID']
        lisc_type = row.get('License Type', '')

        # Trying to Save AI Credits by skipping empty row templates
        if not str(lisc_institute).strip() and not str(lisc_location).strip():
            print(f"Row {i+1} appears empty, skipping.")
            count_processed -= 1
            count_skipped += 1
            continue

        claude_response = ask_claude_for_license_verification(
            lisc_institute, lisc_location, lisc_name, lisc_type)
        target_database, search_term, verify_method = extract_claude_response(
            claude_response)

        # Added a user assist mode for databases requiring human intervention

        if verify_method == "Manual Required":
            print(
                f"\n Row {i+1}: {row['Client Name']} requires a secure portal check ({target_database}). Please choose one of the following:\n")
            print("1. Assist program (Program opens browser, you log in/search, and you log results, program adds result to excel)\n")
            print("2. Flag (Program marks as a 'Come Back To' and moves on)\n")
            print("3. Skip Row  (No change, program skips row.)\n")
            print("4. Exit Program")

            choice = input("Select an option (1, 2, 3, or 4): \n").strip()

            if choice == "1":
                scraped_expiration = web_utils.manual_login_help(
                    target_database, search_term, lisc_id, lisc_name, lisc_location
                )
                data.at[i, 'Status'] = "Verified (Manual Assist)"
                data.at[i, 'Expiration Date'] = str(scraped_expiration)

            elif choice == "2":
                print("Flag Requested! Flagging row for later manual entry...")
                data.at[i, 'Status'] = "Manual Verification Required"
                data.at[i, 'Expiration Date'] = "See Portal"

            elif choice == "4" or choice.lower() in ["exit", "q"]:
                print(f"Exit Requested! Saving Progress at row {i}! ByeBye!")
                count_processed -= 1
                break

            else:
                print(
                    f"Skip Requested! Skipping row {i+1} calculations entirely...\n")
                count_processed -= 1
                count_skipped += 1
                continue

        else:
            scraped_expiration = web_utils.search_registry_for_license(
                database_type=target_database,
                search_query=search_term,
                license_id=lisc_id,
                license_location=lisc_location,
                is_headless=is_headless
            )
            current_time = datetime.now().strftime("%m-%d-%Y @ %I:%M%p")
            data.at[i, 'Database'] = str(target_database)
            data.at[i, 'Status'] = "Pending"
            data.at[i, 'Expiration Date'] = str(scraped_expiration)
            data.at[i, 'Date Verified'] = str(current_time)

        print(
            f"♥ Target located: {target_database} | Search Term: {search_term}")

    # Saving the updated data back to the Excel file after processing all rows.
    data.to_excel(excel_file, index=False)

    print("\nLicense verification process completed. Excel file has been updated with the results.\n")

    # opening the updated Excel file for the user to review.
    print("Opening Excel file!♥")
    os.system(f'start "" "{excel_file}"')

    return {"processed": count_processed,
            "skipped": count_skipped,
            "total": len(data)
            }


def summary_report(progress):
    """Displays the progress of the license verification process."""

    if progress:
        print("\n==================================================")
        print("🎉 WORKFLOW SUMMARY REPORT")
        print("==================================================")
        print(f"   • Total Clients in File:      {progress['total']}")
        print(f"   • AI Strategies Processed:     {progress['processed']}")
        print(f"   • Existing Records Skipped:    {progress['skipped']}")
        print("==================================================\n")

    else:
        print("No file was processed. Please restart the program and select a valid Excel file to proceed. ♥")


def main():
    """Main function to execute the license verification process."""
    clear_console()
    headless_setting = config.config_browser()
    welcome_banner()
    progress = run_license_verification(headless_setting)
    summary_report(progress)


# Main execution:
if __name__ == "__main__":
    main()
