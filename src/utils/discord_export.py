from datetime import datetime
import json
from pathlib import Path

from .. import console


def get_channels_from_folder(folder_path: str) -> dict:
    """Get channel information from the Discord data export folder"""
    try:
        index_path = Path(folder_path) / "messages" / "index.json"

        if not index_path.exists():
            console.print(
                f"[bold red]Error:[/] Could not find index.json at {index_path}"
            )
            raise FileNotFoundError(f"Missing index.json at {index_path}")

        with open(index_path, "r", encoding="utf-8") as f:
            channels_data = json.load(f)

        return channels_data
    except Exception as e:
        console.print(f"[bold red]Error loading channels:[/] {str(e)}")
        raise


def get_channel_messages(folder_path: str, channel_id: str) -> list:
    """Get messages for a specific channel from the Discord data export folder"""
    try:
        messages_path = (
            Path(folder_path) / "messages" / f"c{channel_id}" / "messages.json"
        )

        if not messages_path.exists():
            console.print(
                f"[bold red]Error:[/] Could not find messages.json at {messages_path}"
            )
            raise FileNotFoundError(f"Missing messages.json at {messages_path}")

        with open(messages_path, "r", encoding="utf-8") as f:
            messages_data = json.load(f)

        return messages_data
    except Exception as e:
        console.print(f"[bold red]Error loading channel messages:[/] {str(e)}")
        raise
