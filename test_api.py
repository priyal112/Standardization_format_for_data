from cmath import e
from os import name
from unittest import result
import traceback
from main import create_summary
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient

from main import app, OUTPUT_FOLDER


client = TestClient(app)


def test_api_is_running():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Standardization API is running"
    )


def test_upload_and_standardize_csv():
    
    # Prepare sample CSV with an invalid phone number
    # Prepare sample CSV with phone number variations
    csv_content = (
        b"name,email,active,amount,phone\n"
        b"Priyal,priyal@gmail.com,YES,1250.50,9876543210\n"
        b"Rahul,rahul@gmail.com,YES,1500.00,12345\n"
    )

    response = client.post(
        "/standardize",
        files={
            "file": (
                "test_upload.csv",
                BytesIO(csv_content),
                "text/csv"
            )
        }
    )

    assert response.status_code == 200

    result = response.json()

    assert result["rows_processed"] == 2
    assert result["columns_processed"] == 5
    assert result["summary"]["total_values"] == 10

    # Check review records in API response
    assert "review_records" in result
    assert "review_records_count" in result
    print("Review count:", result["review_records_count"])
    print("Review records:", result["review_records"])
    print("Column profiles:", result["column_profiles"])
    assert result["review_records_count"] >= 1

    assert any(
        record["column"] == "phone"
        and record["rule"] == "LOW_CONFIDENCE_REVIEW"
        for record in result["review_records"]
    )

    # Check output file exists
    output_path = Path(result["output_file"])
    assert output_path.exists()

    # Check log file exists
    log_path = Path(result["log_file"])
    assert log_path.exists()


def test_unsupported_file_type():
    response = client.post(
        "/standardize",
        files={
            "file": (
                "test_upload.txt",
                BytesIO(b"sample content"),
                "text/plain"
            )
        }
    )

    assert response.status_code == 415


if __name__ == "__main__":
    test_functions = [
        test_api_is_running,
        test_upload_and_standardize_csv,
        test_unsupported_file_type,
    ]

    passed = 0
    failed = 0

    for test_function in test_functions:
        try:
            test_function()
            print(f"PASS: {test_function.__name__}")
            passed += 1
        except Exception as error:
            print(f"FAIL: {test_function.__name__}: {error}")
            traceback.print_exc()
            failed += 1

    print(f"\nTotal: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

def test_create_summary():
    logs = [
        {
            "status": "STANDARDIZED",
            "category": "NORMAL_STANDARDIZATION",
            "rule": "EMAIL_STANDARDIZATION"
        },
        {
            "status": "NEEDS_REVIEW",
            "category": "GENUINE_DATA_REVIEW",
            "rule": "LOW_CONFIDENCE_REVIEW"
        }
    ]

    summary = create_summary(logs)

    assert summary["total_values"] == 2
    assert summary["standardized"] == 1
    assert summary["needs_review"] == 1
    assert summary["normal_standardization"] == 1
    assert summary["genuine_data_review"] == 1
    assert summary["rules_applied"]["EMAIL_STANDARDIZATION"] == 1

    print("PASS: test_create_summary")

