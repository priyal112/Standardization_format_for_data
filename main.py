from pathlib import Path
import shutil
import json
import uuid
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from datetime import datetime

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

def create_upload_folder():
    # Generate a unique upload ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]

    upload_id = f"upload_{timestamp}_{unique_id}"

    # Create a separate output folder
    upload_folder = OUTPUT_FOLDER / upload_id
    upload_folder.mkdir(parents=True, exist_ok=False)

    return upload_id, upload_folder


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


def save_output(data, logs, input_file, upload_folder):
    # Preserve the input file format
    extension = Path(input_file).suffix.lower()

    if extension == ".csv":
        output_file = upload_folder / "standardized.csv"
        data.to_csv(output_file, index=False)

    elif extension in {".xlsx", ".xls"}:
        output_file = upload_folder / "standardized.xlsx"
        data.to_excel(output_file, index=False)

    elif extension == ".json":
        output_file = upload_folder / "standardized.json"
        data.to_json(
            output_file,
            orient="records",
            indent=2
        )

    else:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type"
        )

    # Save the detailed processing log
    log_file = upload_folder / "standardization_log.csv"
    pd.DataFrame(logs).to_csv(log_file, index=False)

    return str(output_file), str(log_file)


def create_summary(logs):

    if not logs:
        return {
            "total_values": 0,
            "standardized": 0,
            "already_standard": 0,
            "needs_review": 0,
            "invalid": 0,
            "normal_standardization": 0,
            "genuine_data_review": 0,
            "genuine_data_issue": 0,
            "rules_applied": {}
        }
    
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
    upload_id = uuid.uuid4().hex[:8]
    original_name = Path(safe_filename).stem
    extension = Path(safe_filename).suffix.lower()

    unique_filename = f"{original_name}_{upload_id}{extension}"
    input_file = INPUT_FOLDER / unique_filename

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

    # Create a unique output folder 
    upload_id, upload_folder = create_upload_folder()

    # Create summary
    summary = create_summary(logs)

    # Save standardized output
    output_file, log_file = save_output( 
        data, logs, safe_filename, upload_folder 
    )

    # Save summary as JSON 
    summary_file = upload_folder / "summary.json" 
    with open(summary_file, "w", encoding="utf-8") as file: 
        json.dump(summary, file, indent=2)

    # Return summary
    return {
        "message": "File standardized successfully",
        "upload_id": upload_id,
        "input_file": safe_filename,
        "output_file": str(output_file),
        "log_file": str(log_file),
        "summary_file": str(summary_file),
        "rows_processed": len(data),
        "columns_processed": len(data.columns),
        "column_profiles": profiles,
        "summary": summary
    }