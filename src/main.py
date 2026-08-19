import sys


def main():
    # If arguments are passed (other than script name), run CLI
    if len(sys.argv) > 1:
        from src.cli import app
        app()
    else:
        # Otherwise run GUI
        try:
            from src.gui import run_gui
            run_gui()
        except ImportError as e:
            print(f"Error: Could not start GUI. {e}")
            print("If you are on a headless server, use CLI commands or 'serve' mode.")
            sys.exit(1)

if __name__ == "__main__":
    main()
