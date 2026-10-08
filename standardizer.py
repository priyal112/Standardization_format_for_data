import re
import pandas as pd
from datetime import datetime

def is_null(value):
    # Check if the value is missing
    if value is None:
        return True

    # Check pandas missing values
    try:
        return pd.isna(value)
    except (TypeError, ValueError):
        return False


def standardize_string(value):
    # Convert value to string
    value = str(value)

    # Remove spaces from start and end
    value = value.strip()

    # Replace multiple spaces with one space
    value = re.sub(r"\s+", " ", value)

    return value


def looks_like_email(value):
    # Define a basic email pattern
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    # Check whether value matches email pattern
    return bool(re.match(pattern, value))


def standardize_email(value):
    # Remove extra spaces
    value = value.strip()

    # Convert email to lowercase
    value = value.lower()

    return value


def looks_like_boolean(value):
    # Define accepted boolean values
    boolean_values = {
        "true", "false",
        "yes", "no",
        "y", "n",
        "1", "0"
    }

    # Check whether value is a boolean-like value
    return value.lower() in boolean_values


def standardize_boolean(value):

    value = value.lower().strip()

    # Map true-like values to True
    if value in {"true", "yes", "y", "1"}:
        return True

    # Map false-like values to False
    if value in {"false", "no", "n", "0"}:
        return False

    return value


def looks_like_integer(value):
    # Define an integer pattern
    pattern = r"^[+-]?\d+$"

    # Check integer format
    if not re.match(pattern, value):
        return False

    # Do not convert values with leading zero
    if len(value.lstrip("+-")) > 1 and value.lstrip("+-").startswith("0"):
        return False

    return True


def standardize_integer(value):
    # Remove spaces
    value = value.strip()

    # Convert string to integer
    return int(value)


def looks_like_float(value):
    # Define a decimal number pattern
    pattern = r"^[+-]?\d+\.\d+$"

    # Check whether value is a float
    return bool(re.match(pattern, value))


def standardize_float(value):
    # Remove spaces
    value = value.strip()

    # Remove comma separators
    value = value.replace(",", "")

    # Convert string to float
    return float(value)


def looks_like_phone(value):
    # Keep only digits
    digits = re.sub(r"\D", "", value)

    # Phone should contain 10 to 13 digits
    if not 10 <= len(digits) <= 13:
        return False

    # Require phone formatting or country code
    has_phone_format = any(
        symbol in value
        for symbol in ["+", "-", " ", "(", ")"]
    )

    return has_phone_format


def standardize_phone(value):
    # Keep only digits
    digits = re.sub(r"\D", "", value)

    # Convert Indian 91 prefix to +91
    if len(digits) == 12 and digits.startswith("91"):
        return "+" + digits

    # Add +91 for a 10-digit phone number
    if len(digits) == 10:
        return "+91" + digits

    return "+" + digits

def looks_like_date(value):
    # Define supported date formats
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d-%b-%Y",
        "%d-%B-%Y"
    ]

    # Try each supported format
    for date_format in date_formats:
        try:
            datetime.strptime(value, date_format)
            return True
        except ValueError:
            continue

    return False

def looks_like_date_pattern(value):
    # Check common date separators
    return (
        "/" in value
        or "-" in value
    )

def standardize_date(value):
    # Define supported date formats
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d-%b-%Y",
        "%d-%B-%Y"
    ]

    # Try each format
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(value, date_format)

            # Return ISO date format
            return parsed_date.strftime("%Y-%m-%d")

        except ValueError:
            continue

    # Return original value if conversion fails
    return value


def standardize_value(value):
    # Handle missing values first
    if is_null(value):
        return {
            "value": None,
            "rule": "NULL_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Missing value converted to null"
        }

    # Convert value to string
    text = str(value)

    # Remove unnecessary spaces
    cleaned = standardize_string(text)

    # Check email pattern
    if looks_like_email(cleaned):
        new_value = standardize_email(cleaned)

        return {
            "value": new_value,
            "rule": "EMAIL_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Email converted to lowercase and trimmed"
        }

    # Check boolean pattern
    if looks_like_boolean(cleaned):
        new_value = standardize_boolean(cleaned)

        return {
            "value": new_value,
            "rule": "BOOLEAN_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Boolean value normalized"
        }

    # Check clearly formatted phone
    if looks_like_phone(cleaned):
        new_value = standardize_phone(cleaned)

        return {
            "value": new_value,
            "rule": "PHONE_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Phone formatting normalized"
        }

    # Check integer
    if looks_like_integer(cleaned):
        new_value = standardize_integer(cleaned)

        return {
            "value": new_value,
            "rule": "INTEGER_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Numeric value converted to integer"
        }

    # Check date pattern
    if looks_like_date(cleaned):
        new_value = standardize_date(cleaned)

        return {
            "value": new_value,
            "rule": "DATE_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Date converted to YYYY-MM-DD format"
        }

        # Check if value looks like a date
    if looks_like_date_pattern(cleaned):

        # Check if it is a valid date
        if looks_like_date(cleaned):
            new_value = standardize_date(cleaned)

            return {
                "value": new_value,
                "rule": "DATE_STANDARDIZATION",
                "status": "STANDARDIZED",
                "reason": "Date converted to YYYY-MM-DD format"
            }

        # Do not guess invalid dates
        return {
            "value": cleaned,
            "rule": "INVALID_DATE",
            "status": "INVALID",
            "reason": "Value looks like a date but is not valid"
        }

    # Check float
    if looks_like_float(cleaned):
        new_value = standardize_float(cleaned)

        return {
            "value": new_value,
            "rule": "FLOAT_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Numeric value converted to float"
        }

    # Check ambiguous 10-digit number
    digits = re.sub(r"\D", "", cleaned)

    if len(digits) == 10 and digits.isdigit():
        return {
            "value": cleaned,
            "rule": "AMBIGUOUS_NUMERIC_VALUE",
            "status": "NEEDS_REVIEW",
            "reason": "Could be a phone number or another numeric value"
        }

    # Check generic string changes
    if cleaned != text:
        return {
            "value": cleaned,
            "rule": "STRING_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Extra spaces removed"
        }

    # No change required
    return {
        "value": cleaned,
        "rule": "NO_CHANGE",
        "status": "ALREADY_STANDARD",
        "reason": "No standardization required"
    }