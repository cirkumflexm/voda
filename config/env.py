
from pathlib import Path
import environ
import os

env = environ.Env()
environ.Env.read_env(
        os.path.join(Path(__file__).resolve().parent.parent, '.env'))

SECRET_KEY = env("SECRET_KEY")
SECRET_KEY_DJANGO = env("SECRET_KEY_DJANGO")
SHOP_ID = env("SHOP_ID")
SMSAERO_API_KEY = env("SMSAERO_API_KEY")
SMSAERO_EMAIL = env("SMSAERO_EMAIL")
SMSAERO_TEST_MODE = env("SMSAERO_TEST_MODE")
START_RANGE_PERSONAL_ID = env("START_RANGE_PERSONAL_ID")
NANOMQ_USERNAME = env.str("NANOMQ_USERNAME")
NANOMQ_PASSWORD = env.str("NANOMQ_PASSWORD")
