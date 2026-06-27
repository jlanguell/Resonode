"""Resonode launcher.

The implementation lives in the resonode/ package; this thin shim keeps
`python bot.py` and start.bat working.
"""
from resonode.bot import main

if __name__ == "__main__":
    main()
