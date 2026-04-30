"""owa-graph - Microsoft Graph CLI for one-off queries.

Pipe-friendly: JSON on stdout, logs on stderr, --pretty for humans,
--curl/--az to render the equivalent shell command instead of executing.
The package entry point is `main`, wired up as the `owa-graph` console
script via pyproject.toml. See `cli.py` for the dispatch layer and the
per-concern modules (config, auth, api, emit, format) for the
pure-function pieces.
"""
from .cli import main

__all__ = ["main"]
