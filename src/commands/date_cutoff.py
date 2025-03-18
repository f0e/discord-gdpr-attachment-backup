import click
from datetime import datetime

from .. import console, is_interrupted
from ..utils.gdpr_messages import read_messages_csv, write_messages_csv
from ..utils.discord_export import get_channel_messages


@click.command(name="date-cutoff")
@click.option(
    "-i",
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Path to messages.csv",
)
@click.option(
    "-e",
    "--export_path",
    "export_path",
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Path to Discord data export",
)
@click.option(
    "-d",
    "--date",
    "cutoff_date",
    required=True,
    type=click.DateTime(formats=["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]),
    help="Cutoff date in YYYY-MM-DD or YYYY-MM-DD HH:MM:SS format",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    required=True,
    type=click.Path(),
)
def date_cutoff(
    input_path: str, export_path: str, cutoff_date: datetime, output_path: str
):
    """Remove messages with timestamp after a specific date from messages.csv"""
    console.print("[bold green]Discord GDPR messages.csv date filter[/]")

    try:
        console.print("Reading messages.csv...")
        messages_data = read_messages_csv(input_path)
        console.print(f"Filtering out messages with date after {cutoff_date}...")

        filtered_messages = {}
        removed_count = 0
        retained_count = 0

        # Process each channel
        for channel_id, message_ids in messages_data.items():
            if is_interrupted():
                return

            filtered_messages[channel_id] = []

            try:
                # Get channel messages for timestamp information
                channel_messages = get_channel_messages(export_path, channel_id)
                message_map = {str(msg["ID"]): msg for msg in channel_messages}

                for message_id in message_ids:
                    if message_id not in message_map:
                        continue

                    message = message_map[message_id]
                    timestamp_str = message.get("Timestamp", "")

                    if timestamp_str:
                        try:
                            message_date = datetime.strptime(
                                timestamp_str, "%Y-%m-%d %H:%M:%S"
                            )
                            if message_date > cutoff_date:
                                removed_count += 1
                                continue
                        except ValueError:
                            console.print(
                                f"[yellow]Warning: Could not parse timestamp for message {message_id}, keeping it[/]"
                            )
                    else:
                        # Keep message if no timestamp or can't parse timestamp
                        console.print("No timestamp? keeping")

                    filtered_messages[channel_id].append(message_id)
                    retained_count += 1
            except Exception as e:
                console.print(
                    f"[yellow]Error processing channel {channel_id}: {str(e)}.[/]"
                )
                raise

        # Write filtered messages
        console.print(f"Writing filtered messages to {output_path}...")
        write_messages_csv(filtered_messages, output_path)

        console.print(
            f"[bold green]Completed: {removed_count} messages removed, {retained_count} messages retained[/]"
        )

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise
