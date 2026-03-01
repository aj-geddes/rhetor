"""Rhetor — The Master Orator for Your Documents.

Entry point for the Rhetor desktop application.
"""

def main() -> None:
    """Launch the Rhetor application."""
    from app import RhetorApp

    app = RhetorApp()
    app.run()


if __name__ == "__main__":
    main()
