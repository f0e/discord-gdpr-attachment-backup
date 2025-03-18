import signal
import sys
from rich.console import Console

console = Console()

interrupted = False


def is_interrupted():  # just fuck you python
    global interrupted
    return interrupted


def signal_handler(sig, frame):
    global interrupted
    if not interrupted:
        console.print("[blue]Interrupt received.[/]")
        interrupted = True
    else:
        console.print("[bold red]Forced exit.[/]")
        sys.exit(1)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
