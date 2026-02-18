import sys
from src.cli import app
from src.gui import run_gui

if __name__ == "__main__":
    # If arguments are passed (other than script name), run CLI
    if len(sys.argv) > 1:
        app()
    else:
        # Otherwise run GUI
        run_gui()
