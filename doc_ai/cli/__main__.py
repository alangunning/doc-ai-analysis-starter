from __future__ import annotations

import sys
import traceback

from . import SETTINGS, _interactive_shell, app, console, print_banner


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print_banner()
        args = sys.argv[1:]
        if SETTINGS["verbose"] and "--verbose" not in args and "-v" not in args:
            args.append("--verbose")
        try:
            app(prog_name="cli", args=args)
        except Exception as exc:  # pragma: no cover - runtime error display
            if SETTINGS["verbose"]:
                traceback.print_exc()
            else:
                console.print(f"[red]{exc}[/red]")
    else:
        _interactive_shell()
