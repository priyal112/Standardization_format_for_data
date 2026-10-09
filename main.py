from pathlib import Path
import shutil

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from standardizer import (
    profile_column, standardize_value_by_type, classify_result, CONFIDENCE_THRESHOLD
)


# Create FastAPI application
app = FastAPI(title="Data Standardization API")


# Define folders
INPUT_FOLDER = Path("input")
OUTPUT_FOLDER = Path("output")


# Create folders if they do not exist
INPUT_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)


def read_file(file_path):
    # Get file extension
    extension = file_path.suffix.lower()

    try:
        # Read CSV file
        if extension == ".csv":
            return pd.read_csv(file_path, dtype=object)

        # Read Excel file
        elif extension in [".xlsx", ".xls"]:
            return pd.read_excel(file_path, dtype=object)

        # Read JSON file
        elif extension == ".json":
            return pd.read_json(file_path)

        # Reject unsupported files
        else:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {extension}"
            )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read file: {str(error)}"
        )


def standardize_data(data):
    # Store standardization logs
    logs = []

    # Store column profiles
    profiles = {}

    # Profile every column
    for column in data.columns:

        # Detect column type
        profile = profile_column(
            data[column].tolist()
        )

        # Store profile
        profiles[column] = profile

    # Process every row
    for row_index in data.index:

        # Process every column
        for column in data.columns:

            # Get original value
            original_value = data.at[
                row_index,
                column
            ]

            # Get column profile
            profile = profiles[column]

            # Get detected type
            detected_type = profile["detected_type"]

            # Get confidence
            confidence = profile["confidence"]

            # Apply type-based rule only
            # when confidence is high enough
            if confidence >= CONFIDENCE_THRESHOLD:

                result = standardize_value_by_type(
                    original_value,
                    detected_type
                )

            else:

                result = {
                    "value": original_value,
                    "rule": "LOW_CONFIDENCE_REVIEW",
                    "status": "NEEDS_REVIEW",
                    "reason": (
                        f"Column type confidence "
                        f"is only {confidence}%"
                    )
                }

            category = classify_result(result)

            data.at[row_index, column] = result["value"]

            logs.append({
                "row": row_index + 1,
                "column": column,
                "detected_type": detected_type,
                "confidence": confidence,
                "original_value": original_value,
                "standardized_value": result["value"],
                "rule": result["rule"],
                "status": result["status"],
                "category": category,
                "reason": result["reason"]
            })

    return data, logs, profiles


def save_output(data, logs, input_file):
    # Get original file extension
    extension = input_file.suffix.lower()

    # Get original file name
    file_name = input_file.stem

    # Create output file name
    output_name = f"{file_name}_standardized"

    # Save CSV
    if extension == ".csv":
        output_file = OUTPUT_FOLDER / f"{output_name}.csv"
        data.to_csv(output_file, index=False)

    # Save Excel
    elif extension in [".xlsx", ".xls"]:
        output_file = OUTPUT_FOLDER / f"{output_name}.xlsx"
        data.to_excel(output_file, index=False)

    # Save JSON
    elif extension == ".json":
        output_file = OUTPUT_FOLDER / f"{output_name}.json"
        data.to_json(
            output_file,
            orient="records",
            indent=4
        )

    # Create standardization log
    log_file = OUTPUT_FOLDER / "standardization_log.csv"

    log_data = pd.DataFrame(logs)
    log_data.to_csv(log_file, index=False)

    return output_file, log_file


def create_summary(logs):
    # Convert logs to DataFrame
    log_data = pd.DataFrame(logs)

    # Count status values
    status_counts = log_data["status"].value_counts()

    # Count categories
    category_counts = log_data["category"].value_counts()

    # Count rules
    rule_counts = log_data["rule"].value_counts()

    return {
        "total_values": len(log_data),

        "standardized": int(
            status_counts.get("STANDARDIZED", 0)
        ),

        "already_standard": int(
            status_counts.get("ALREADY_STANDARD", 0)
        ),

        "needs_review": int(
            status_counts.get("NEEDS_REVIEW", 0)
        ),

        "invalid": int(
            status_counts.get("INVALID", 0)
        ),

        "normal_standardization": int(
            category_counts.get(
                "NORMAL_STANDARDIZATION",
                0
            )
        ),

        "genuine_data_review": int(
            category_counts.get(
                "GENUINE_DATA_REVIEW",
                0
            )
        ),

        "genuine_data_issue": int(
            category_counts.get(
                "GENUINE_DATA_ISSUE",
                0
            )
        ),

        "rules_applied": {
            rule: int(count)
            for rule, count
            in rule_counts.items()
        }
    }


@app.get("/")
def home():
    # Test API status
    return {
        "message": "Standardization API is running"
    }


@app.post("/standardize")
async def standardize_file(
    file: UploadFile = File(...)
):
    # Check file name
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    # Get only the file name
    safe_filename = Path(file.filename).name

    # Create uploaded file path
    input_file = INPUT_FOLDER / safe_filename

    # Save uploaded file
    with input_file.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Check if file is empty
    if input_file.stat().st_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty"
        )

    # Read uploaded file
    data = read_file(input_file)

    # Check if data is empty
    if data.empty:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file contains no records"
        )

    # Standardize the data
    standardized_data, logs, profiles = standardize_data(data)

    # Create summary
    summary = create_summary(logs)

    # Save standardized output
    output_file, log_file = save_output(
        standardized_data,
        logs,
        input_file
    )

    # Return summary
    return {
        "message": "File standardized successfully",
        "input_file": safe_filename,
        "output_file": str(output_file),
        "log_file": str(log_file),
        "rows_processed": len(data),
        "columns_processed": len(data.columns),
        "column_profiles": profiles,
        "summary": summary
    }