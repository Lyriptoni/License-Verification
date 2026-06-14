"""This script reads an Excel file containing client information, processes each client's license status, and updates the Excel file with the verification results.
It checks if the client's license is active and updates the status, expiry date, and verification date accordingly."""

import os
import time
import shutil
import pandas as pd
import config
import web_utils
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from inputimeout import inputimeout, TimeoutOccurred
from traceback import print_stack
from typing import final
from winsound import PlaySound
from pydoc import plain
from tkinter import filedialog, Tk
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
from config import ExcelColumns


load_dotenv()  # Load environment variables from .env file

claude_client = Anthropic(api_key=os.getenv("CLAUDE_KEY"))

# Methods:


def clear_console():
    """Clears the console for better readability."""
    os.system('cls' if os.name == 'nt' else 'clear')


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

    for line in banner.splitlines():
        web_utils.print_style(line, type_effects=True, delay=0.02)


def select_excel_file():
    """Opens a file dialog for the user to select an Excel file."""
    root = Tk()
    root.withdraw()  # Hide the root window
    # Bug Fix: Making sure the window opens for sure!
    root.attributes('-topmost', True)

    web_utils.print_style(
        "Please select the Excel file containing client license information for verification.\n", type_effects=True)

    file_path = filedialog.askopenfilename(
        parent=root,
        title="Select Excel File",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )

    if not file_path:
        return None
    print(f"Selected file: {file_path}\n")
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
        ExcelColumns.CLIENT, ExcelColumns.INSTITUTION, ExcelColumns.LOCATION,
        ExcelColumns.LIC_NAME, ExcelColumns.ON_NURSYS, ExcelColumns.LIC_ID,
        ExcelColumns.LIC_TYPE, ExcelColumns.LIC_STATUS, ExcelColumns.VERIF_STATUS,
        ExcelColumns.ISSUE_DATE, ExcelColumns.ACCREDITED, ExcelColumns.EXP_DATE,
        ExcelColumns.REVIEW_DATE, ExcelColumns.DATE_VERIFIED, ExcelColumns.COMPACT,
        ExcelColumns.DATABASES
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


def color_excel(file_path):
    """Used for color coding the excel based on status"""

    try:
        # Loading excel to memory
        wb = load_workbook(file_path)
        ws = wb.active

        # Setting Colors

        red_error_fill = PatternFill(
            start_color="FFFF0000", end_color="FFFF0000", fill_type="solid")
        blue_comeback_fill = PatternFill(
            start_color="FF00FFFF", end_color="FF00FFFF", fill_type="solid")
        green_completed_fill = PatternFill(
            start_color="FF00FF00", end_color="FF00FF00", fill_type="solid")
        grey_skipped_fill = PatternFill(
            start_color="FF9B9A9A", end_color="FF9B9A9A", fill_type="solid")

        # Find status column
        status_col = None
        for col in range(1, ws.max_column + 1):
            if ws.cell(row=1, column=col).value == ExcelColumns.VERIF_STATUS:
                status_col = col
                break

        if status_col:
            # Loop through every row and paint it!
            for row in range(2, ws.max_row + 1):
                status_text = str(
                    ws.cell(row=row, column=status_col).value).lower()

                target_fill = None
                if "error" in status_text or "flagged" in status_text:
                    target_fill = red_error_fill
                elif "verified" in status_text or "processed" in status_text:
                    target_fill = green_completed_fill
                elif "manual" in status_text or "come back to" in status_text:
                    target_fill = blue_comeback_fill
                elif "skipped" in status_text:
                    target_fill = grey_skipped_fill

                # If a match is found, paint every cell in that specific row
                if target_fill:
                    for col in range(1, ws.max_column + 1):
                        ws.cell(row=row, column=col).fill = target_fill

        wb.save(file_path)

    except Exception as e:
        web_utils.print_style(
            f"Formatting warning: Could not apply colors ({e})")


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
    1. CRITICAL: If the Location is clearly outside of the United States (e.g., Japan, Canada), set TARGET DATABASE to 'International Registry' and METHOD to 'Manual Required'.
    2. If the Location is in the US AND the request is to verify an academic degree or an educational program's status (including Nursing, Pharmacy, or Dietitian tracks), set TARGET DATABASE to 'DAPIP' and METHOD to 'Automatic'.
    3. If the row is looking to verify an individual person's live nursing license number (like an RN or LPN active license), set TARGET DATABASE to 'NURSYS' and METHOD to 'Manual Required'.
    4. If it is an individual medical practitioner not covered above, determine the exact state board (e.g., 'Texas Medical Board') and set METHOD to 'Manual Required'.

    RULES FOR CLEANED SEARCH TERM:
    1. If TARGET DATABASE is 'DAPIP', the CLEANED SEARCH TERM must ONLY be the core name of the school or institution. Strip out trailing branch locations, cities, states, or zip codes.
    2. If it is an individual person, clean up their name to just 'Firstname Lastname'.

    RULES FOR VERIFICATION METHOD:
    1. Set METHOD to 'Automatic' ONLY for DAPIP.
    2. Set METHOD to 'Manual Required' for NURSYS, International Registry, State Medical Boards, or registries requiring individual user logins.

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


def ask_claude_to_parse_scraped_text(plain_scraped_text, institution_name, license_name, license_type, location):
    """Asking Claude to analyze a website page text to find the expiration date for us"""

    if len(plain_scraped_text) < 50:
        return plain_scraped_text

    prompt = f"""
    You are an expert data parsing assistant.
    Analyze the following raw text scraped from an institutional accreditation profile page:

    --- RAW WEB TEXT ---
    {plain_scraped_text}
    --------------------

    YOUR TASK:
    Locate the specific accreditation timelines for this exact profile:
    - Institution: {institution_name}
    - Campus Location: {location}
    - Program/License: {license_name}
    - Type: {license_type}

    CRITICAL LOOKUP RULES:
    1. MULTIPLE CAMPUSES: If multiple campuses or affiliated schools are listed in the text, you MUST only extract data for the specific campus matching the 'Campus Location'.
    2. PROGRAM MATCH: You must find the specific row for the exact program requested (e.g., if DNP or Master's is requested, completely ignore the Baccalaureate row and grab the DNP row).
    3. CCNE REGISTRY LOGIC: If this text is from the CCNE registry, the expiration date is listed under 'Accreditation Term Expires'. CCNE pages do NOT have a formal review date, so if it's CCNE, you MUST output N/A for REVIEW.

    CRITICAL COMPLIANCE FORMAT RULE:
    You must extract ONLY the raw dates (MM/DD/YYYY format if possible).
    Respond in this strict, single-line format with a pipe separator character. Do not include extra text characters or sentences:
    EXPIRATION: [Date or N/A] | REVIEW: [Date or N/A]
    """
    response = claude_client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=50,
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


def fetch_parse_data(row, search_term, target_database, is_headless):
    """Function for executing browser 'reading'. Asks Claude for date extraction.."""
    raw_scraped_collection = web_utils.search_registry_for_license(
        database_type=target_database,
        search_query=search_term,
        license_id=row[ExcelColumns.LIC_ID],
        license_location=row[ExcelColumns.LOCATION],
        is_headless=is_headless
    )

    web_utils.print_style(
        "Extracting the official date...\n", type_effects=True, delay=0.05)
    scraped_expiration = ask_claude_to_parse_scraped_text(
        raw_scraped_collection,
        row[ExcelColumns.INSTITUTION],
        row[ExcelColumns.LIC_NAME],
        row.get(ExcelColumns.LIC_TYPE, 'N/A'),
        row[ExcelColumns.LOCATION]
    )

    # Setting Defaults to fall back on

    final_expire_date = "N/A"
    final_review_date = "N/A"

    # In case the AI returns # or *

    if "#" in scraped_expiration or "*" in scraped_expiration:
        lines = scraped_expiration.split("\n")
        valid_lines = [
            l for l in lines if "EXPIRATION:" in l or "|" in l]

        # Making sure valid_line is there.
        if len(valid_lines) > 0:
            scraped_expiration = valid_lines[0]

        else:
            # Fallback Statement for Claude
            scraped_expiration = "EXPIRATION: N/A | REVIEW: N/A"

        scraped_expiration = scraped_expiration.replace(
            "#", "").replace("*", "").strip()

    try:
        if "|" in scraped_expiration:
            sections = scraped_expiration.split("|")
            exp_sec = sections[0].replace("EXPIRATION:", "").strip()
            rev_sec = sections[1].replace("REVIEW:", "").strip()

            final_expire_date = web_utils.date_correcter(
                exp_sec) if exp_sec != "N/A" else "N/A"
            final_review_date = web_utils.date_correcter(
                rev_sec) if rev_sec != "N/A" else "N/A"

        else:
            final_expire_date = web_utils.date_correcter(
                scraped_expiration)

    except Exception as parse_fail:
        web_utils.print_style(
            f"Oop- Need to check this out: {parse_fail}")

        final_expire_date = "N/A"

    return final_expire_date, final_review_date


def process_auto_route(row, i, is_headless):
    """
    Determines the pathway for a row and routes it to the correct handler.
    Tries DAPIP Registry and if it fails, then tries CCNE Registry.
    If both fail or it's unknown credential, it will require manual required.
    """

    lisc_institute = row[ExcelColumns.INSTITUTION]
    lisc_location = row[ExcelColumns.LOCATION]
    lisc_name = row[ExcelColumns.LIC_NAME]
    lisc_id = row[ExcelColumns.LIC_ID]
    lisc_type = row.get(ExcelColumns.LIC_TYPE, '')

    # Skip empty row templates to save API credits
    if not str(lisc_institute).strip() and not str(lisc_location).strip():
        web_utils.print_style(f"Row {i+1} appears empty, skipping.")
        return "Skipped", "N/A", "N/A", "N/A"

    # Asking Claude for search location
    claude_response = ask_claude_for_license_verification(
        lisc_institute, lisc_location, lisc_name, lisc_type)

    ai_suggest_database, search_term, verify_method = extract_claude_response(
        claude_response)

    # If row needs to be manually or it's location is international
    if verify_method == "Manual Required" or ai_suggest_database == "International Registry":
        return "Manual Required", "N/A", "N/A", ai_suggest_database

    # Fetching Data from Claude here:

    # Starting with DAPIP, as it's the primary site for the purpose of the program.

    final_expire_date, final_review_date = fetch_parse_data(
        row, search_term, "DAPIP", is_headless)
    verified_database = "DAPIP"

    # If DAPIP came back with no date, we try CCNE..
    if final_expire_date == "N/A" and final_review_date == "N/A":
        # Let user know what's happening before swapping
        web_utils.print_style("Didn't find anything on DAPIP...\n")

        final_expire_date, final_review_date = fetch_parse_data(
            row, search_term, "CCNE", is_headless)
        verified_database = "CCNE Portal"

    # Determine Status
    if final_expire_date != "N/A" or final_review_date != "N/A":
        if lisc_type != "" and lisc_type != "N/A":
            current_status = "Verified (Programmatic)"
        else:
            current_status = "Verified (Institutional)"
    else:
        current_status = "Unknown / Flagged"

    return current_status, final_expire_date, final_review_date, verified_database


def run_license_verification(is_headless):
    """Main function to run the license verification process."""

    excel_file = select_excel_file()

    if not excel_file:
        web_utils.print_style(
            "No Excel file selected. Ending process.\n", type_effects=True, delay=0.05)
        web_utils.print_style(
            "Please restart and select a file to proceed. ♥\n", type_effects=True, delay=0.05)
        return None

    backup_excel_file(excel_file)

    # Read all data as strings to avoid issues with NaN values
    raw_data = pd.read_excel(excel_file, dtype=str)
    web_utils.print_style(
        "\nExcel file loaded successfully.\n", type_effects=True)
    data = clean_excel_data(raw_data)

    # Allows User to choose how to complete the task:

    web_utils.print_style("==================================================")
    web_utils.print_style("How Do We Want to Work Today?:", delay=0.02)
    web_utils.print_style(
        "==================================================\n")
    time.sleep(0.5)
    web_utils.print_style(
        "1. AI Does Most of the Work (Automated Research and Verification via Claude AI)\n", delay=0.02)
    web_utils.print_style(
        "2. I'll Do the Research Myself, thank you! (You do the research, Claude assist with data entry)\n", delay=0.02)
    web_utils.print_style("3. Exit Program", delay=0.02)
    time.sleep(1)
    print("=======================================================================================================\n")
    mode_choice = input("Your choice is? (1, 2, or 3):\n\n ").strip()

    # If choices
    if mode_choice == "3" or mode_choice.lower() in ["exit", "q"]:
        web_utils.print_style("\nExit Requested! ByeBye!♥",
                              type_effects=True, delay=0.05)
        return None

    # Tracking progress counters:
    count_processed = 0
    count_skipped = 0

    if mode_choice == "1":
        web_utils.print_style("\n 🤖 ...Calling Claude for assistance... 🤖\n",
                              type_effects=True)
        time.sleep(1)

    for i, row in data.iterrows():
        # Checking if status is not empty first.
        if str(row[ExcelColumns.VERIF_STATUS]).strip() != "":
            web_utils.print_style(
                f"Row {i + 1}: {row[ExcelColumns.CLIENT]}'s status is already set. Completed already? Skipping...\n")
            count_skipped += 1
            continue

        current_time = datetime.now().strftime("%m-%d-%Y @ %I:%M%p")

        # Manual Mode
        if mode_choice == "2":
            web_utils.print_style(
                "\n===================================================================")
            web_utils.print_style(
                "Rapid Fire Mode: \nHere's what we're working with: \n", type_effects=True, delay=0.05)
            web_utils.print_style(
                "===================================================================")
            web_utils.print_style(
                f"Row {i+1}: Data Entry for {row[ExcelColumns.CLIENT]}!\n")
            web_utils.print_style(
                f"Institution: {row[ExcelColumns.INSTITUTION]} | {row[ExcelColumns.LOCATION]} | License ID: {row[ExcelColumns.LIC_ID]}")
            print(
                "===========================================================================================\n")
            web_utils.print_style(
                "We're looking for the expiration date... Or, press Enter to skip this row!:\n")
            user_date_entered = input("Enter the Expiration Date:\n ")

            if user_date_entered.lower() in ["exit", "q"]:
                web_utils.print_style(
                    f"Exit requested, saving progress at row {i}", type_effects=True)
                count_processed -= 1
                break

            data.at[i, ExcelColumns.VERIF_STATUS] = "Manually Processed"
            data.at[i, ExcelColumns.EXP_DATE] = web_utils.date_correcter(
                user_date_entered)
            data.at[i, ExcelColumns.DATE_VERIFIED] = str(current_time)
            data.at[i, ExcelColumns.DATABASES] = "Manual Entry Deck"
            count_processed += 1
            continue

        # Automated Mode
        web_utils.print_style(
            f"Processing new Client: {row[ExcelColumns.CLIENT]}", delay=0.05)
        count_processed += 1

        # Row context
        result_status, exp_date, rev_date, active_db = process_auto_route(
            row, i, is_headless)

        # Skip Option
        if result_status == "Skipped":
            web_utils.print_style(
                f"Skip Requested! Skipping row {i+1} calculations entirely...\n", type_effects=True, delay=0.05)
            count_processed -= 1
            count_skipped += 1
            continue

        # Manual Choice handles
        if result_status == "Manual Required":
            web_utils.print_style(
                f"\n Row {i+1}: {row[ExcelColumns.CLIENT]} requires user assistance! ({active_db}). Please choose one of the following:\n", type_effects=True, delay=0.05)
            web_utils.print_style(
                "1. Assist program (Program opens browser, you log in/search, and you log results, program adds result to excel)\n", delay=0.05)
            web_utils.print_style(
                "2. Flag (Program marks as a 'Come Back To' and moves on)\n", delay=0.05)
            web_utils.print_style(
                "3. Skip Row  (No change, program skips row.)\n", delay=0.05)
            web_utils.print_style(
                "4. Exit Program", delay=0.05)

            # Timeout after 30 seconds, auto-picks Option 2.) Flag
            try:
                choice = inputimeout(
                    prompt="Select an option (1, 2, 3, or 4): \n", timeout=30).strip()
            except TimeoutOccurred:
                web_utils.print_style(
                    "\n⏰ Timeout reached! Auto-flagging for later...\n", type_effects=True, delay=0.05)
                choice = "2"

            if choice == "1":
                web_utils.print_style(
                    "\nAssist Program selected!\n", type_effects=True)

                scraped_expiration = web_utils.manual_login_help(active_db,
                                                                 row[ExcelColumns.INSTITUTION], row[ExcelColumns.LIC_ID],
                                                                 row[ExcelColumns.LIC_NAME], row[ExcelColumns.LOCATION]
                                                                 )
                data.at[i,
                        ExcelColumns.VERIF_STATUS] = "Verified (Manual Assist)"
                data.at[i, ExcelColumns.EXP_DATE] = str(scraped_expiration)
                data.at[i, ExcelColumns.DATE_VERIFIED] = str(current_time)
                data.at[i, ExcelColumns.DATABASES] = str(active_db)

            elif choice == "2":
                web_utils.print_style(
                    "\nFlag Requested! Flagging row for later manual entry...\n", delay=0.05)
                data.at[i, ExcelColumns.VERIF_STATUS] = "Manual Verification Required"
                data.at[i, ExcelColumns.EXP_DATE] = "COME BACK TO"
                data.at[i, ExcelColumns.DATE_VERIFIED] = str(current_time)
                data.at[i, ExcelColumns.DATABASES] = str(active_db)

            elif choice == "4" or choice.lower() in ["exit", "q"]:
                web_utils.print_style(
                    f"\nExit Requested! Saving Progress at row {i}! ByeBye!", type_effects=True, delay=0.05)
                break

            else:
                web_utils.print_style(
                    "\nSkip Requested! Leaving row untouched..\n", delay=0.05)
                count_processed -= 1
                count_skipped += 1
                continue

        # Saving Auto Progress
        data.at[i, ExcelColumns.DATABASES] = str(active_db)
        data.at[i, ExcelColumns.VERIF_STATUS] = str(result_status)
        data.at[i, ExcelColumns.EXP_DATE] = str(exp_date)
        data.at[i, ExcelColumns.REVIEW_DATE] = str(rev_date)
        data.at[i, ExcelColumns.DATE_VERIFIED] = str(current_time)

        web_utils.print_style(
            f"♥ Target located: {active_db} | Search Term: {row[ExcelColumns.INSTITUTION]} | Expiration Date: {exp_date} | Next Review Date: {rev_date}\n", delay=0.1)

    # Use Retry Function:
    data = retry_flagged_rows(data, excel_file, is_headless)

    # Saving the updated data back to the Excel file after processing all rows.
    data.to_excel(excel_file, index=False)

    # Colors Excel
    color_excel(excel_file)

    web_utils.print_style(
        "\nLicense verification process completed. Excel file has been updated with the results.\n", type_effects=True)

    # opening the updated Excel file for the user to review.
    web_utils.print_style("Opening Excel file!♥", type_effects=True)
    os.system(f'start "" "{excel_file}"')

    return {"processed": count_processed,
            "skipped": count_skipped,
            "total": len(data)
            }


def retry_flagged_rows(data, excel_file, is_headless):
    """
    Scans the excel for incomplete verifications and offers the user 
    an option to retry them before finalizing the Excel file.
    """
    # Defining what warrants a retry
    current_time = datetime.now().strftime("%m-%d-%Y @ %I:%M%p")
    flagged_statuses = ["Unknown / Flagged",
                        "Manual Verification Required", "Skipped", "ERROR", ""]

    # Checking if there are any that need to be retried.
    needs_retry = data[ExcelColumns.VERIF_STATUS].isin(flagged_statuses).any()

    if not needs_retry:
        return data  # Everything is fine.

    # Prompt
    web_utils.print_style(
        "\n==================================================")
    web_utils.print_style(" Check Again Option: ")
    web_utils.print_style(
        "==================================================\n")
    web_utils.print_style(
        "There are rows marked as Flagged, Skipped, or Error.")
    retry_choice = input(
        "Would you like to do these rows now? (y/n): ").strip().lower()

    # Loop
    if retry_choice == 'y':
        web_utils.print_style(
            "\n🔄 Restarting row scan...\n", type_effects=True)

        for i, row in data.iterrows():
            if row[ExcelColumns.VERIF_STATUS] in flagged_statuses:

                # Temporarily clear the status so the loop doesn't skip it
                data.at[i, ExcelColumns.VERIF_STATUS] = ""

                # Restart auto route
                result_status, exp_date, rev_date, active_db = process_auto_route(
                    row, i, is_headless)

                # Update with new results matching the V1.1 schema
                data.at[i, ExcelColumns.DATABASES] = str(active_db)
                data.at[i, ExcelColumns.VERIF_STATUS] = str(result_status)
                data.at[i, ExcelColumns.EXP_DATE] = str(exp_date)
                data.at[i, ExcelColumns.REVIEW_DATE] = str(rev_date)
                data.at[i, ExcelColumns.DATE_VERIFIED] = str(current_time)

                web_utils.print_style(
                    f"♥ Retry completed for row {i+1}\n", delay=0.1)

    return data


def summary_report(progress):
    """Displays the progress of the license verification process."""

    if progress:
        print("\n==================================================")
        print("🎉 WORKFLOW SUMMARY REPORT")
        print("==================================================")
        time.sleep(2)
        web_utils.print_style(
            f"   • Total Clients in File:      {progress['total']}", type_effects=True)
        web_utils.print_style(
            f"   • AI Strategies Processed:     {progress['processed']}", type_effects=True)
        web_utils.print_style(
            f"   • Existing Records Skipped:    {progress['skipped']}", type_effects=True)
        time.sleep(1)
        print("==================================================\n")
        time.sleep(2)
        web_utils.print_style(
            "Thank you for your time! ♥\n\nByeBye!", type_effects=True)

    else:
        web_utils.print_style(
            "No file was processed. Please restart the program and select a valid Excel file to proceed. ♥", type_effects=True)


def main():
    """Main function to execute the license verification process."""
    clear_console()
    headless_setting = config.config_browser()
    welcome_banner()
    progress = run_license_verification(headless_setting)

    if progress is None:
        return

    summary_report(progress)


# Main execution:
if __name__ == "__main__":
    main()
