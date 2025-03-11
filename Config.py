from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Description: Configuration file for the bot

# Token
API_KEY = os.getenv('API_KEY')

# on pythonanywhere server
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# VIPS ID  Faramarz, Farzaneh, Arash
VIPS_ID = [int(id) for id in os.getenv('VIPS_ID').split(',')]

# Mahsa ID
MAHSA_ID = int(os.getenv('MAHSA_ID'))

# Admin ID
ADMIN_ID = [int(id) for id in os.getenv('ADMIN_ID').split(',')]

# Support ID
SUPPORT_ID = int(os.getenv('SUPPORT_ID'))

# Variables
texts = {}
price = 0

### Text configs

# mahsa
mahsa_config = os.getenv('MAHSA_CONFIG')
# vip
vip_config = os.getenv('VIP_CONFIG')