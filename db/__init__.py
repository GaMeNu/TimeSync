import os
from dotenv import load_dotenv

load_dotenv()

HOME_DIR = os.getenv("HOME_DIR")

__version__ = '1.0.0'
if HOME_DIR is not None:
    __filename__ = os.path.join(HOME_DIR, 'global_clock_db.sqlite3')
else:
    __filename__ = None

__user__ = os.getenv("USERNAME")
__pass__ = os.getenv("PASSWORD")
