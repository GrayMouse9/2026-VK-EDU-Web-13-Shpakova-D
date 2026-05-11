import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'application.settings')

    BASE_DIR = Path(__file__).resolve().parent

    _ENV_FILE = os.environ.get('DJANGO_ENV_FILE')

    if _ENV_FILE and (BASE_DIR / _ENV_FILE).exists():
        load_dotenv(BASE_DIR / _ENV_FILE)
    elif (BASE_DIR / '.env.local').exists():
        load_dotenv(BASE_DIR / '.env.local')
    else:
        load_dotenv(BASE_DIR / '.env')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
