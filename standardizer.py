import re
import pandas as pd
from rules import RULE_CATALOG
from config import STANDARDIZATION_CONFIG

# Minimum confidence required for standardization
CONFIDENCE_THRESHOLD = (
    STANDARDIZATION_CONFIG["confidence"]["minimum"]
)


def is_null(value):
    # Check missing values
    return value is None or pd.isna(value)


def standardize_string(value):
    # Convert value to string
    value = str(value)

    # Remove extra spaces
    value = value.strip()

    # Replace multiple spaces with one
    value = re.sub(r"\s+", " ", value)

    return value


def looks_like_email(value):
    # Check email pattern
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(re.match(pattern, value))


def standardize_email(value):
    # Remove spaces and lowercase email
    return value.strip().lower()


def looks_like_boolean(value):
    # Define accepted boolean values
    true_values = {"true", "yes", "y", "1"}
    false_values = {"false", "no", "n", "0"}

    value = value.strip().lower()

    return value in true_values or value in false_values


def standardize_boolean(value):
    # Normalize boolean value
    value = value.strip().lower()

    if value in {"true", "yes", "y", "1"}:
        return True

    return False


def looks_like_integer(value):
    # Remove surrounding spaces
    value = value.strip()

    # Check integer format
    return bool(
        re.match(r"^[+-]?\d+$", value)
    )


def standardize_integer(value):
    # Convert value to integer
    return int(value)


def looks_like_float(value):
    # Remove surrounding spaces
    value = value.strip()

    cleaned = value.replace(",", "")

    # Check decimal format
    return bool(
        re.match(
            r"^[+-]?\d+\.\d+$",
            cleaned
        )
    )


def standardize_float(value):
    # Remove comma separators
    value = value.replace(",", "")

    return float(value)

def looks_like_numeric(value):
    # Remove surrounding spaces
    value = value.strip()

    cleaned = value.replace(",", "")

    # Check integer or decimal
    return bool(
        re.match(
            r"^[+-]?\d+(\.\d+)?$",
            cleaned
        )
    )

def looks_like_phone(value):
    # Extract digits
    digits = re.sub(r"\D", "", value)

    # Check phone length
    if not 10 <= len(digits) <= 13:
        return False

    # Require phone-like formatting
    has_phone_format = any(
        symbol in value
        for symbol in ["+", "-", " ", "(", ")"]
    )

    return has_phone_format


def standardize_phone(value):
    # Read phone configuration
    phone_config = STANDARDIZATION_CONFIG["phone"]

    country_code = phone_config["default_country_code"]
    number_length = phone_config["default_number_length"]

    # Keep only digits
    digits = re.sub(r"\D", "", value)

    # Add default country code
    if len(digits) == number_length:
        return country_code + digits

    # Remove + from configured country code
    country_digits = country_code.replace("+", "")

    # Handle existing country code
    if digits.startswith(country_digits):
        return "+" + digits

    # Keep existing country code
    return "+" + digits


def looks_like_date(value):
    # Supported date formats
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d-%b-%Y",
        "%d-%B-%Y"
    ]

    for date_format in date_formats:
        try:
            pd.to_datetime(
                value,
                format=date_format
            )
            return True
        except (ValueError, TypeError):
            continue

    return False


def looks_like_date_pattern(value):
    # Check whether value looks date-like
    return "/" in value or "-" in value


def standardize_date(value):
    # Supported date formats
    date_formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d-%b-%Y",
        "%d-%B-%Y"
    ]

    for date_format in date_formats:
        try:
            date_value = pd.to_datetime(
                value,
                format=date_format
            )

            output_format = (
                STANDARDIZATION_CONFIG["date"]["output_format"]
)
            return date_value.strftime(output_format)

        except (ValueError, TypeError):
            continue

    return value


def standardize_value(value):
    # Handle missing value
    if is_null(value):
        return {
            "value": None,
            "rule": "NULL_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Missing value converted to null"
        }

    # Clean value
    cleaned = standardize_string(value)

    # Email
    if looks_like_email(cleaned):
        standardized = standardize_email(cleaned)

        return {
            "value": standardized,
            "rule": "EMAIL_STANDARDIZATION",
            "status": (
                "STANDARDIZED"
                if standardized != cleaned
                else "ALREADY_STANDARD"
            ),
            "reason": "Email converted to lowercase and spaces removed"
        }

    # Boolean
    if looks_like_boolean(cleaned):
        standardized = standardize_boolean(cleaned)

        return {
            "value": standardized,
            "rule": "BOOLEAN_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Boolean value normalized"
        }

    # Phone
    if looks_like_phone(cleaned):
        standardized = standardize_phone(cleaned)

        return {
            "value": standardized,
            "rule": "PHONE_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Phone number normalized"
        }

    # Date
    if looks_like_date(cleaned):
        standardized = standardize_date(cleaned)

        return {
            "value": standardized,
            "rule": "DATE_STANDARDIZATION",
            "status": (
                "STANDARDIZED"
                if standardized != cleaned
                else "ALREADY_STANDARD"
            ),
            "reason": "Date converted to YYYY-MM-DD"
        }

    # Invalid date-like value
    if looks_like_date_pattern(cleaned):
        return {
            "value": cleaned,
            "rule": "INVALID_DATE",
            "status": "INVALID",
            "reason": "Value looks like a date but is not valid"
        }

    # Integer
    if looks_like_integer(cleaned):

        numeric_part = cleaned.lstrip("+-")

        # Avoid changing IDs with leading zeros
        if (
            len(numeric_part) > 1
            and numeric_part.startswith("0")
        ):
            return {
                "value": cleaned,
                "rule": "INTEGER_REVIEW",
                "status": "NEEDS_REVIEW",
                "reason": "Leading zeros may represent an ID or code"
            }

        return {
            "value": standardize_integer(cleaned),
            "rule": "INTEGER_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Numeric value converted to integer"
        }

    # Float
    if looks_like_float(cleaned):
        return {
            "value": standardize_float(cleaned),
            "rule": "FLOAT_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Decimal value converted to float"
        }

    # Possible phone or numeric identifier
    if cleaned.isdigit() and len(cleaned) == 10:
        return {
            "value": cleaned,
            "rule": "NUMERIC_REVIEW",
            "status": "NEEDS_REVIEW",
            "reason": "Could be a phone number or another numeric value"
        }

    # Generic string
    return {
        "value": cleaned,
        "rule": "STRING_STANDARDIZATION",
        "status": (
            "STANDARDIZED"
            if cleaned != str(value)
            else "ALREADY_STANDARD"
        ),
        "reason": "Extra spaces removed"
    }


def detect_value_type(value):
    # Handle missing values
    if is_null(value):
        return "NULL"

    # Clean value
    cleaned = standardize_string(value)

    # Detect email
    if looks_like_email(cleaned):
        return "EMAIL"

    # Detect boolean
    if looks_like_boolean(cleaned):
        return "BOOLEAN"

    # Detect phone
    if looks_like_phone(cleaned):
        return "PHONE"

    # Detect date
    if looks_like_date(cleaned):
        return "DATE"

    # Detect float
    if looks_like_float(cleaned):
        return "FLOAT"

    # Detect integer
    if looks_like_integer(cleaned):
        return "INTEGER"

    # Default type
    return "STRING"


def profile_column(values):
    # Store detected types
    detected_types = []

    # Check every value
    for value in values:

        value_type = detect_value_type(value)

        # Ignore null values
        if value_type != "NULL":
            detected_types.append(value_type)

    # Handle empty column
    if not detected_types:
        return {
            "detected_type": "UNKNOWN",
            "confidence": 0,
            "distribution": {}
        }

    # Count each detected type
    type_counts = pd.Series(
        detected_types
    ).value_counts()

    # Get dominant type
    dominant_type = type_counts.index[0]

    # Calculate confidence
    confidence = (
        type_counts.iloc[0]
        / len(detected_types)
    ) * 100

    # Convert distribution to dictionary
    distribution = {
        data_type: int(count)
        for data_type, count
        in type_counts.items()
    }

    return {
        "detected_type": dominant_type,
        "confidence": round(confidence, 2),
        "distribution": distribution
    }


def standardize_value_by_type(
    value,
    detected_type
):
    # Handle missing value
    if is_null(value):
        return {
            "value": None,
            "rule": "NULL_STANDARDIZATION",
            "status": "STANDARDIZED",
            "reason": "Missing value converted to null"
        }

    # Clean value
    cleaned = standardize_string(value)

    # Email rule
    if detected_type == "EMAIL":

        if looks_like_email(cleaned):

            standardized = standardize_email(cleaned)

            return {
                "value": standardized,
                "rule": "EMAIL_STANDARDIZATION",
                "status": (
                    "STANDARDIZED"
                    if standardized != cleaned
                    else "ALREADY_STANDARD"
                ),
                "reason": (
                    "Email converted to lowercase "
                    "and spaces removed"
                )
            }

    # Boolean rule
    if detected_type == "BOOLEAN":

        if looks_like_boolean(cleaned):

            standardized = standardize_boolean(cleaned)

            return {
                "value": standardized,
                "rule": "BOOLEAN_STANDARDIZATION",
                "status": "STANDARDIZED",
                "reason": "Boolean value normalized"
            }

    # Phone rule
    if detected_type == "PHONE":

        if looks_like_phone(cleaned):

            standardized = standardize_phone(cleaned)

            return {
                "value": standardized,
                "rule": "PHONE_STANDARDIZATION",
                "status": "STANDARDIZED",
                "reason": "Phone number normalized"
            }

    # Date rule
    if detected_type == "DATE":

        if looks_like_date(cleaned):

            standardized = standardize_date(cleaned)

            return {
                "value": standardized,
                "rule": "DATE_STANDARDIZATION",
                "status": (
                    "STANDARDIZED"
                    if standardized != cleaned
                    else "ALREADY_STANDARD"
                ),
                "reason": "Date converted to YYYY-MM-DD"
            }

    # Integer rule
    if detected_type == "INTEGER":

        if looks_like_integer(cleaned):

            numeric_part = cleaned.lstrip("+-")

            # Protect possible IDs
            if (
                len(numeric_part) > 1
                and numeric_part.startswith("0")
            ):
                return {
                    "value": cleaned,
                    "rule": "INTEGER_REVIEW",
                    "status": "NEEDS_REVIEW",
                    "reason": (
                        "Leading zeros may represent "
                        "an ID or code"
                    )
                }

            return {
                "value": standardize_integer(cleaned),
                "rule": "INTEGER_STANDARDIZATION",
                "status": "STANDARDIZED",
                "reason": "Numeric value converted to integer"
            }

    # Float rule
    if detected_type == "FLOAT":

        if looks_like_float(cleaned):

            standardized = standardize_float(cleaned)

            return {
                "value": standardized,
                "rule": "FLOAT_STANDARDIZATION",
                "status": "STANDARDIZED",
                "reason": "Decimal value converted to float"
            }

    return standardize_value(value)

def classify_result(result):
    # Get rule name
    rule = result["rule"]

    # Find rule configuration
    rule_config = RULE_CATALOG.get(rule)

    # Return configured category
    if rule_config:
        return rule_config["category"]

    # Unknown rule
    return "UNKNOWN"