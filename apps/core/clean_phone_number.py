def clean_phone_number(phone_number):
    """Clean the phone number by removing any non-numeric characters."""
    cleaned_number = ""

    if phone_number.startswith("+"):
        cleaned_number = phone_number[1:]
    elif phone_number.startswith("0"):
        cleaned_number = f"254{phone_number[1:]}"
    else:
        cleaned_number = phone_number

    return cleaned_number



