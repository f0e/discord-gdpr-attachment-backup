import json
import os
import signal
import sys
from collections import defaultdict
from enum import Enum
from pathlib import Path
from urllib.parse import unquote, urlparse

import click
import requests
from rich.console import Console

console = Console()

interrupted = False


def signal_handler(sig, frame):
    global interrupted
    if not interrupted:
        console.print(
            "[blue]Interrupt received. Completing current download and exiting gracefully...[/]"
        )
        interrupted = True
    else:
        console.print("[bold red]Forced exit. Some downloads may be incomplete.[/]")
        sys.exit(1)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@click.command()
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
    "-o",
    "--output",
    "output_path",
    default="out",
    type=click.Path(),
    help="Path to save files",
)
def main(input_path: str, export_path: str, output_path: str):
    console.print("[bold green]Discord GDPR messages.csv attachment downloader[/]")

    try:
        console.print("Getting messages...")
        deleting_messages = get_deleting_messages(input_path)
        console.print("Getting channels...")
        channels = get_channels_from_folder(export_path)
        console.print("Done with preparation.")

        files_downloaded = 0
        files_skipped = 0
        files_failed = 0

        for channel_id, message_ids in deleting_messages.items():
            if interrupted:
                break

            if channel_id not in channels:
                console.print(
                    f"[yellow]Channel {channel_id} not found in export data, skipping[/]"
                )
                continue

            channel = channels[channel_id]
            channel_messages = get_channel_messages(export_path, channel_id)
            console.print(f"Processing channel: {channel}, {len(message_ids)} messages")

            for message in channel_messages:
                if interrupted:
                    break

                message_id = str(message["ID"])

                if message_id not in message_ids:
                    continue

                if message["Attachments"]:
                    attachments = message["Attachments"].split(" ")
                    for i, attachment_url in enumerate(attachments):
                        if interrupted:
                            break

                        result = download_attachment(
                            i, attachment_url, channel_id, message_id, output_path
                        )
                        if result == DownloadStatus.DOWNLOADED:
                            files_downloaded += 1
                        elif result == DownloadStatus.SKIPPED:
                            files_skipped += 1
                        elif result == DownloadStatus.FAILED:
                            files_failed += 1

        console.print(
            f"[bold green]Completed: {files_downloaded} files downloaded, {files_skipped} files skipped, {files_failed} files failed[/]"
        )

        if interrupted:
            console.print("[blue]Process was interrupted but exited gracefully.[/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        if not interrupted:
            raise


def get_deleting_messages(messages_path: str) -> dict[str, list]:
    try:
        if not Path(messages_path).exists():
            console.print(
                f"[bold red]Error:[/] Could not find messages.csv at {messages_path}"
            )
            raise FileNotFoundError(f"Missing messages.csv at {messages_path}")

        message_data = defaultdict(list)

        with open(messages_path, "r", encoding="utf-8") as f:
            for line in f:
                channel_id, message_id = line.strip().split(",")
                message_data[channel_id].append(message_id)

        return message_data
    except Exception as e:
        console.print(f"[bold red]Error loading messages:[/] {str(e)}")
        raise


def get_channels_from_folder(folder_path: str):
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


def get_channel_messages(folder_path: str, channel_id: str):
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


class DownloadStatus(Enum):
    DOWNLOADED = "downloaded"
    SKIPPED = "skipped"
    FAILED = "failed"


def download_attachment(
    attachment_index: int,
    attachment_url: str,
    channel_id: str,
    message_id: str,
    output_path: str,
) -> DownloadStatus:
    parsed_url = urlparse(attachment_url)
    filename = os.path.basename(parsed_url.path)
    filename = unquote(filename)

    attachment_out_path = (
        Path(output_path)
        / channel_id
        / message_id
        / f"attachment {attachment_index + 1}"
        / filename
    )

    if attachment_out_path.exists() and attachment_out_path.suffix != ".py":
        console.print(
            f"[yellow]File already downloaded: {attachment_out_path}, skipping.[/]"
        )
        return DownloadStatus.SKIPPED

    attachment_out_path.parent.mkdir(parents=True, exist_ok=True)

    response = requests.get(attachment_url, stream=True, timeout=30)

    if response.status_code == 200:
        with open(attachment_out_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        console.print(f"[green]File downloaded: {attachment_out_path}[/]")
        return DownloadStatus.DOWNLOADED
    else:
        console.print(
            f"[red]Failed to download file. Status code: {response.status_code}. URL: {attachment_url}[/]"
        )
        return DownloadStatus.FAILED


if __name__ == "__main__":
    main()
