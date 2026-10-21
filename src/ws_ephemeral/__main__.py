"""Allow `python -m ws_ephemeral`."""

from .cli import app

if __name__ == "__main__":
    app(prog_name="ws-ephemeral")
