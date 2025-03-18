from pathlib import Path

from .. import console


def read_messages_csv(messages_path: str) -> dict:
    """Read messages.csv and return a dictionary of channel_id to message_ids"""
    try:
        if not Path(messages_path).exists():
            console.print(
                f"[bold red]Error:[/] Could not find messages.csv at {messages_path}"
            )
            raise FileNotFoundError(f"Missing messages.csv at {messages_path}")

        message_data = {}

        with open(messages_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 2:
                    channel_id, message_id = parts[0], parts[1]
                    if channel_id not in message_data:
                        message_data[channel_id] = []
                    message_data[channel_id].append(message_id)

        return message_data
    except Exception as e:
        console.print(f"[bold red]Error loading messages:[/] {str(e)}")
        raise


def write_messages_csv(messages_data: dict, output_path: str) -> None:
    """Write messages data to a CSV file"""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for channel_id, message_ids in messages_data.items():
                for message_id in message_ids:
                    f.write(f"{channel_id},{message_id}\n")
        console.print(f"[green]Successfully wrote messages to {output_path}[/]")
    except Exception as e:
        console.print(f"[bold red]Error writing messages:[/] {str(e)}")
        raise
