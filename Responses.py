# import requests
# import logging
# import Config as Keys

# Text responses
def sample_responses(input_text):
    # Cleaning input
    last_value = input_text.text
    user_message = str(last_value).lower()

    # Hello
    if user_message in ('hi', 'hello', 'hey', 'salam', 'slm', 'سلام', 'سلم'):
        return "سلام ارادت 🫡"

    # Secret Hello
    if user_message in ('привет', 'priviet', 'پریویت'):
        return "Priviet Azizam 🙃❤️"

    else:
        return "متوجه نشدم! 🤔"
