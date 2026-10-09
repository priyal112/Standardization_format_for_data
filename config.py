# Standardization configuration

STANDARDIZATION_CONFIG = {

    "phone": {
        "default_country_code": "+91",
        "default_number_length": 10,
        "allow_country_code_prefix": True
    },

    "date": {
        "output_format": "%Y-%m-%d",
        "input_formats": [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d-%b-%Y",
            "%d-%B-%Y"
        ],
        "ambiguous_date_policy": "review"
    },

    "confidence": {
        "minimum": 80
    }
}