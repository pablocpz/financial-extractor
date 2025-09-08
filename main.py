from __future__ import annotations
from file_data_extraction import file_data_extraction
from agent_field_matching import field_matching
from excel_exporting import export_excel
import sys
import os
import argparse


def main():
    parser = argparse.ArgumentParser(description="Process PDF reports and export data.")
    parser.add_argument("reports_folder", type=str, help="Folder with input PDFs")
    parser.add_argument("out_folder", type=str, help="Output folder for markdown/json")
    args = parser.parse_args()

    reports_folder = args.reports_folder
    out_folder = args.out_folder

    # Step 1: Extract data from PDFs to markdown
    print("\n=== Step 1: Extracting data from PDFs ===")
    file_data_extraction(reports_folder_name=reports_folder, output_folder_name=out_folder)

    # Step 2: Match fields using LLM and save as JSON
    print("\n=== Step 2: Matching fields with LLM ===")
    field_matching(DATA_FOLDER=out_folder)

    # Step 3: Export all JSONs to Excel
    print("\n=== Step 3: Exporting to Excel ===")
    final_excel = export_excel(out_dir=out_folder)
    if final_excel:
        print(f"\nFinal Excel written to: {final_excel}")
    else:
        print("\nNo Excel file was generated.")

if __name__ == "__main__":
    main()