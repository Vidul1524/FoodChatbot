# This module provides utility functions to help with string processing and session ID extraction,
# which are used by your FastAPI application

import re


# Convert a dictionary of food items and their quantities into a readable string format.
def get_str_from_food_dict(food_dict: dict):
    result = ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])
    #  Joins all formatted strings with a comma and space (, ).
    return result # single string representing all food items and their quantities, e.g., "2 Burgers, 1 Fries"


# Extracts the session ID from a given session string.
def extract_session_id(session_str: str):
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(0)
        return extracted_string  # extracted session ID if a match is found

    return ""
