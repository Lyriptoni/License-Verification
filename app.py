"""This script reads an Excel file containing client information, processes each client's license status, and updates the Excel file with the verification results.
It checks if the client's license is active and updates the status, expiry date, and verification date accordingly."""

import os
import shutil
import pandas as pd
from tkinter import filedialog, Tk
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()  # Load environment variables from .env file

claude_client = Anthropic(api_key=os.getenv("CLAUDE_KEY"))


def ask_claude_for_license_verification(institution, location, license_name):
    """Sends a request to Claude for license verification using public data and returns the response."""
    prompt = f"""

    You are a helpful assistant that verifies client license information using publicly available data.
    Please verify the license information for the following client:

    Institution: {institution}
    Location: {location}
    License Name: {license_name}

    Analyze this data and determine the correct registry pathway.
    If the location is in the United States, your target database is DAPIP.
    If the location is international (like Japan), your target database is an International Registry.
    
    Respond in this exact, strict format:
    TARGET DATABASE: [DAPIP or International Registry]
    CLEANED SEARCH TERM: [The exact school name cleaned up for search bars]
    """

    response = claude_client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()


print("\n Sending test request to Claude for license verification...\n")
test_result = ask_claude_for_license_verification(
    "Japan Institute of Culinary Arts", "Tokyo, Japan", "Certification of Food Safety in Japan"
)

print(f"Claude's response: \n\n{test_result}\n")

# def clear_console():
#     """Clears the console for better readability."""
#     os.system('cls' if os.name == 'nt' else 'clear')


# clear_console()
# print("Starting License Verification Process...\n")


# def select_excel_file():
#     """Opens a file dialog for the user to select an Excel file."""
#     root = Tk()
#     root.withdraw()  # Hide the root window

#     print("Please select the Excel file containing client license information for verification.")

#     file_path = filedialog.askopenfilename(
#         title="Select Excel File",
#         filetypes=[("Excel files", "*.xlsx *.xls")]
#     )

#     if not file_path:
#         print("No file selected. Exiting.")
#         return None
#     print(f"Selected file: {file_path}")
#     return file_path


# def backup_excel_file(file_path):
#     """Creates a backup of the Excel file before making any changes."""
#     # Creating folder for backup if it doesn't exist
#     if not os.path.exists("backup"):
#         os.makedirs("backup")

#     # Getting the base name of the file
#     base_name = os.path.basename(file_path)

#     # Splitting the name and extension
#     name_without_ext = os.path.splitext(base_name)[0]

#     timestamp = datetime.now().strftime("%m%d%Y_%H%M%S")
#     backup_file_name = f"backup/{name_without_ext}_Backup_{timestamp}.xlsx"

#     if os.path.exists(file_path):
#         shutil.copy(file_path, backup_file_name)
#         print(f"Backup created: {backup_file_name}")

# # Main execution flow


# excel_file = select_excel_file()

# if excel_file:

#     backup_excel_file(excel_file)

#     data = pd.read_excel(excel_file)

#     print("\nExcel file loaded successfully.\n")
#     print(data.head())  # Print the first few rows of the data for verification

#     for column_label in ["Client Name", "Institution", "Location", "License Name", "Status", "Expiration Date", "Date Verified"]:
#         # Ensuring all columns are treated as strings for proper checking
#         data[column_label] = data[column_label].astype(str)
#         # Replacing 'nan' with empty string for better handling of missing values
#         data[column_label] = data[column_label].replace("nan", "")

# # lisc_institute = row['Institution']
# # lisc_name = row['License Name']
# # lisc_id = row['License ID']


# print("\n Rows: \n")

# for i, row in data.iterrows():

#     if not pd.isna(row["Status"]):  # Checking if status is not empty first.
#         print(f"Row {i + 1}: {row['Client Name']} is verified already")
#         continue

#     print(f"Processing new Client: {row['Client Name']}")

#     # Testing

#     test_status = "Active"
#     test_expiry = "12-31-2024"

#     # Writing to excel file

#     current_time = datetime.now().strftime("%m-%d-%Y @ %I:%M%p")
#     data.at[i, 'Status'] = test_status
#     data.at[i, 'Expiration Date'] = test_expiry
#     data.at[i, 'Date Verified'] = current_time

# data.to_excel(excel_file, index=False)

# print("Opening Excel file!")
#  # This will open the updated Excel file after processing is complete.
# os.system(f'start "" "{excel_file}"')
