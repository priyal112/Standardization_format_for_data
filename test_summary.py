from main import get_review_records
from main import create_summary


def test_empty_logs():
    summary = create_summary([])

    assert summary["total_values"] == 0
    assert summary["standardized"] == 0
    assert summary["needs_review"] == 0
    assert summary["rules_applied"] == {}


def test_mixed_statuses():
    logs = [
        {
            "status": "STANDARDIZED",
            "category": "NORMAL_STANDARDIZATION",
            "rule": "INTEGER_STANDARDIZATION"
        },
        {
            "status": "ALREADY_STANDARD",
            "category": "NORMAL_STANDARDIZATION",
            "rule": "STRING_STANDARDIZATION"
        },
        {
            "status": "NEEDS_REVIEW",
            "category": "GENUINE_DATA_REVIEW",
            "rule": "PHONE_REVIEW"
        },
        {
            "status": "NEEDS_REVIEW",
            "category": "GENUINE_DATA_REVIEW",
            "rule": "PHONE_REVIEW"
        }
    ]

    summary = create_summary(logs)

    assert summary["total_values"] == 4
    assert summary["standardized"] == 1
    assert summary["already_standard"] == 1
    assert summary["needs_review"] == 2

    assert summary["standardized_percentage"] == 25.0
    assert summary["already_standard_percentage"] == 25.0
    assert summary["needs_review_percentage"] == 50.0

    assert summary["rules_applied"]["PHONE_REVIEW"] == 2


def test_review_records():
    logs = [
        {
            "row": 3,
            "column": "phone",
            "original_value": "12345",
            "detected_type": "PHONE",
            "confidence": 100.0,
            "rule": "PHONE_REVIEW",
            "status": "NEEDS_REVIEW",
            "reason": "Unexpected phone length"
        },
        {
            "row": 1,
            "column": "amount",
            "original_value": "250",
            "detected_type": "INTEGER",
            "confidence": 100.0,
            "rule": "INTEGER_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Integer converted"
        }
    ]

    result = get_review_records(logs)

    assert len(result) == 1
    assert result[0]["column"] == "phone"
    assert result[0]["rule"] == "PHONE_REVIEW"


def test_empty_review_records():
    assert get_review_records([]) == []


if __name__ == "__main__":
    test_empty_logs()
    test_mixed_statuses()
    test_review_records()
    test_empty_review_records()

    print("PASS: test_empty_logs")
    print("PASS: test_mixed_statuses")
    print("PASS: test_review_records")
    print("PASS: test_empty_review_records")
    print("All summary and review tests passed!")


