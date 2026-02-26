from dotenv import load_dotenv
import os


def get_database_url():
    """ Function to get database_url """
    load_dotenv()
    return os.getenv('DATABASE_URL')
