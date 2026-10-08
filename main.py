from pathlib import Path
import pandas as pd

from standardizer import standardize_value


# Define the input folder
INPUT_FOLDER = Path("input")

# Define the output folder
OUTPUT_FOLDER = Path("output")


def find_input_file():
    # Get all files from input folder
    files = list(INPUT_FOLDER.iterdir())

    # Keep only actual files
    files = [file for file in files if file.is_file()]

    if not files:
        raise FileNotFoundError("No file found in input folder.")

    return files[0]


def read_file(file_path):
    # Get file extension
    extension = file_path.suffix.lower()

    # Read CSV
    if extension == ".csv":
        return pd.read_csv(file_path, dtype=object)

    # Read Excel
    elif extension in [".xlsx", ".xls"]:
        return pd.read_excel(file_path, dtype=object)

    # Read JSON
    elif extension == ".json":
        return pd.read_json(file_path)

    # Stop for unsupported files
    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )


def standardize_data(data):
    # Create an empty list for logs
    logs = []

    # Go through every row
    for row_index in data.index:

        # Go through every column
        for column in data.columns:

            # Get original value
            original_value = data.at[row_index, column]

            # Standardize the value
            result = standardize_value(original_value)

            # Update the DataFrame
            data.at[row_index, column] = result["value"]

            # Store the standardization information
            logs.append({
              "row": row_index + 1,
              "column": column,
              "original_value": original_value,
              "standardized_value": result["value"],
              "rule": result["rule"],
              "status": result["status"],
              "reason": result["reason"]
            })

    return data, logs


def save_output(data, logs, input_file):
    # Create output folder if it does not exist
    OUTPUT_FOLDER.mkdir(exist_ok=True)

    # Get original file extension
    extension = input_file.suffix.lower()

    # Get original file name without extension
    file_name = input_file.stem

    # Create standardized file name
    output_name = f"{file_name}_standardized"

    # Save CSV as CSV
    if extension == ".csv":
        output_file = OUTPUT_FOLDER / f"{output_name}.csv"
        data.to_csv(output_file, index=False)

    # Save Excel as XLSX
    elif extension in [".xlsx", ".xls"]:
        output_file = OUTPUT_FOLDER / f"{output_name}.xlsx"
        data.to_excel(output_file, index=False)

    # Save JSON as JSON
    elif extension == ".json":
        output_file = OUTPUT_FOLDER / f"{output_name}.json"
        data.to_json(output_file, orient="records", indent=4)

    # Stop if file type is unsupported
    else:
        raise ValueError(
            f"Unsupported output format: {extension}"
        )

    # Convert logs into DataFrame
    log_data = pd.DataFrame(logs)

    # Always keep log in CSV format
    log_file = OUTPUT_FOLDER / "standardization_log.csv"

    # Save standardization log
    log_data.to_csv(log_file, index=False)

    # Display output locations
    print(f"\nStandardized file: {output_file}")
    print(f"Standardization log: {log_file}")


def main():
    # Find input file
    input_file = find_input_file()

    # Display input file
    print(f"Input file: {input_file}")

    # Read input file
    data = read_file(input_file)

    # Display original information
    print(f"Rows: {len(data)}")
    print(f"Columns: {len(data.columns)}")

    # Standardize all values
    data, logs = standardize_data(data)

    # Save the results
    save_output(data, logs, input_file)

    # Display completion message
    print("\nStandardization completed successfully!")


if __name__ == "__main__":
    # Start the program
    main()