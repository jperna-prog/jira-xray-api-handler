lst=[ "Adrian Prizont",
"Alejandro Scarpatti",
"Ariel.etchepare",
"Cristian Goldenhorn",
"Daniel Rodriguez",
"daniel.guerra",
"elizabeth.elman",
"Fernando Biancardi",
"Gaston Tabares",
"Jorge Zembo",
"juan.perna",
"Julian Piquin",
"LAURA.CANTERO",
"Nicolas Pardo",
"Odemara Montes",
"Osorio, Leonel Alberto",
"Sergio Moramarco",
"Sergio Motta",
"Silvia Navarrane",
"Sueiro, Paula"
]

import pandas as pd
import os

def add_binary_column_from_list(
    file_path: str,
    column_to_check: str,
    lookup_list: list,
    new_column_name: str
):
    """
    Loads an Excel file, checks if values in a specified column exist 
    within a Python reference list, and adds a binary column (1 or 0) 
    with the result.

    Args:
        file_path (str): Path to the Excel file (.xlsx or .csv).
        column_to_check (str): Name of the Excel column containing the keys (e.g., 'Key').
        lookup_list (list): The list of reference values (e.g., [JIRA-100, JIRA-200, ...]).
        new_column_name (str): The name for the new binary column.
    """
    if not os.path.exists(file_path):
        print(f"ERROR: File not found at path: {file_path}")
        return

    try:
        # Load the file (assumes data is on the first sheet)
        df = pd.read_excel(file_path)
    except Exception:
        # If .xlsx read fails, try reading as .csv
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"ERROR: Could not read the file. Ensure it is a valid Excel (.xlsx) or CSV. Detail: {e}")
            return

    if column_to_check not in df.columns:
        print(f"ERROR: Column '{column_to_check}' was not found in the file.")
        return

    # 1. Apply the vectorized lookup logic
    # The .isin() method returns a Boolean Series (True/False).
    # .astype(int) converts True to 1 and False to 0.
    df[new_column_name] = df[column_to_check].isin(lookup_list).astype(int)

    # 2. Save the file, creating a new updated file
    output_filename = file_path.replace(".xlsx", "_updated.xlsx")
    df.to_excel(output_filename, index=False)
    
    print(f"SUCCESS: Column '{new_column_name}' added.")
    print(f"The updated report was saved as: {output_filename}")
    print(f"Total matches found (value 1): {df[new_column_name].sum()}")


# --- USAGE EXAMPLE ---

if __name__ == "__main__":
    # 1. Define the reference list (Simulates your list of target Jira reports)
    TARGET_JIRA_LIST = lst

    # 2. Define the file parameters
    REPORT_FILE_NAME = "consolidated_report.xlsx"   # Your primary output file
    KEY_COLUMN_IN_EXCEL = "Reporter Name"           # The column containing the Jira keys (e.g., SDI-101)
    NEW_COLUMN = "Traditional"                      # The name for the new 1/0 column

    # Call the function (Example is commented out until you provide the file)
    add_binary_column_from_list( file_path=REPORT_FILE_NAME,
          column_to_check=KEY_COLUMN_IN_EXCEL,
          lookup_list=TARGET_JIRA_LIST,
          new_column_name=NEW_COLUMN
     )

    print("\n⚠️ Note: The __main__ block is commented out. Uncomment to test.")