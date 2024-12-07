import subprocess
import os

# Ensure we are in the correct directory (where `manage.py` is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def runserver():
    try:
        # Run 'python manage.py runserver'
        subprocess.run(['python', 'manage.py', 'runserver'], cwd=BASE_DIR, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    runserver()
