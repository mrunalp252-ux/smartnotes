import os
import sys

# Ensure the root directory is on Python's path so app and dependencies resolve
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Vercel serverless function entrypoint
if __name__ == '__main__':
    app.run()
