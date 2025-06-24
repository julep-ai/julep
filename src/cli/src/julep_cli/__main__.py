try:
    from julep_cli.app import app
except ImportError:
    from .app import app

if __name__ == "__main__":
    app()
