# Standardization rule catalog

RULE_CATALOG = {

    "STRING_STANDARDIZATION": {
        "category": "NORMAL_STANDARDIZATION",
        "description": "Remove extra spaces from text",
        "automatic": True
    },

    "EMAIL_STANDARDIZATION": {
        "category": "NORMAL_STANDARDIZATION",
        "description": "Trim spaces and convert email to lowercase",
        "automatic": True
    },

    "PHONE_STANDARDIZATION": {
        "category": "NORMAL_STANDARDIZATION",
        "description": "Normalize phone number format",
        "automatic": True
    },

    "BOOLEAN_STANDARDIZATION": {
        "category": "NORMAL_STANDARDIZATION",
        "description": "Convert boolean representations to True or False",
        "automatic": True
    },

    "DATE_STANDARDIZATION": {
        "category": "NORMAL_STANDARDIZATION",
        "description": "Convert dates to YYYY-MM-DD",
        "automatic": True
    },

    "INTEGER_STANDARDIZATION": {
        "category": "NORMAL_STANDARDIZATION",
        "description": "Convert valid integer values to integer type",
        "automatic": True
    },

    "FLOAT_STANDARDIZATION": {
        "category": "NORMAL_STANDARDIZATION",
        "description": "Convert decimal values to float type",
        "automatic": True
    },

    "NULL_STANDARDIZATION": {
        "category": "NORMAL_STANDARDIZATION",
        "description": "Convert missing values to null",
        "automatic": True
    },

    "INTEGER_REVIEW": {
        "category": "GENUINE_DATA_REVIEW",
        "description": "Leading zeros may represent an ID or code",
        "automatic": False
    },

    "NUMERIC_REVIEW": {
        "category": "GENUINE_DATA_REVIEW",
        "description": "Numeric value may represent different data types",
        "automatic": False
    },

    "LOW_CONFIDENCE_REVIEW": {
        "category": "GENUINE_DATA_REVIEW",
        "description": "Column type confidence is too low",
        "automatic": False
    },

    "INVALID_DATE": {
        "category": "GENUINE_DATA_ISSUE",
        "description": "Value looks like a date but is invalid",
        "automatic": False
    },


    "AMBIGUOUS_DATE_REVIEW": {
        "category": "GENUINE_DATA_REVIEW",
        "description": "Date has multiple valid interpretations",
        "automatic": False
    },

    "PHONE_REVIEW": {
        "category": "GENUINE_DATA_REVIEW",
        "description": "Phone number has an unexpected length or format",
        "auto": False
    }

}