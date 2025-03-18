import click

from .. import console, is_interrupted
from ..utils.downloads import download_attachment, DownloadStatus
from ..utils.gdpr_messages import read_messages_csv
from ..utils.discord_export import get_channels_from_folder, get_channel_messages


@click.command(name="download-attachments")
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
def download_attachments(input_path: str, export_path: str, output_path: str):
    """Download attachments from messages listed in messages.csv"""
    console.print("[bold green]Discord GDPR messages.csv attachment downloader[/]")

    try:
        console.print("Getting messages...")
        messages_data = read_messages_csv(input_path)
        console.print("Getting channels...")
        channels = get_channels_from_folder(export_path)
        console.print("Done with preparation.")

        files_downloaded = 0
        files_skipped = 0
        files_failed = 0

        for channel_id, message_ids in messages_data.items():
            if is_interrupted():
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
                if is_interrupted():
                    break

                message_id = str(message["ID"])

                if message_id not in message_ids:
                    continue

                if message.get("Attachments"):
                    attachments = message["Attachments"].split(" ")
                    for i, attachment_url in enumerate(attachments):
                        if is_interrupted():
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

        if is_interrupted():
            console.print("[blue]Process was interrupted but exited gracefully.[/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        if not is_interrupted():
            raise
