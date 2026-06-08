"""This script reads an Excel file containing client information, processes each client's license status, and updates the Excel file with the verification results.
It checks if the client's license is active and updates the status, expiry date, and verification date accordingly."""

import os
import shutil
import pandas as pd
from tkinter import filedialog, Tk
from datetime import datetime


def clear_console():
    """Clears the console for better readability."""
    os.system('cls' if os.name == 'nt' else 'clear')


clear_console()
print("Starting License Verification Process...\n")


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

# Main execution flow


excel_file = select_excel_file()

if excel_file:

    backup_excel_file(excel_file)

    data = pd.read_excel(excel_file)

    print("\nExcel file loaded successfully.\n")
    print(data.head())  # Print the first few rows of the data for verification

    for column_label in ["Client Name", "Institution", "Location", "License Name", "Status", "Expiration Date", "Date Verified"]:
        # Ensuring all columns are treated as strings for proper checking
        data[column_label] = data[column_label].astype(str)
        # Replacing 'nan' with empty string for better handling of missing values
        data[column_label] = data[column_label].replace("nan", "")

# lisc_institute = row['Institution']
# lisc_name = row['License Name']
# lisc_id = row['License ID']


print("\n Rows: \n")

for i, row in data.iterrows():

    if not pd.isna(row["Status"]):  # Checking if status is not empty first.
        print(f"Row {i + 1}: {row['Client Name']} verified already")
        continue

    print(f"Processing new Client: {row['Client Name']}")

    # Testing

    test_status = "Active"
    test_expiry = "12-31-2024"

    # Writing to excel file

    data.at[i, 'Status'] = test_status
    data.at[i, 'Expiration Date'] = test_expiry
    data.at[i, 'Date Verified'] = datetime.now().strftime("%m-%d-%Y")

data.to_excel(excel_file, index=False)
print("\nUpdated Excel Data: \n")
print(data)
