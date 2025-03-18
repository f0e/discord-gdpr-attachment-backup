import os
from pathlib import Path
from urllib.parse import unquote, urlparse
import requests

from .. import console


class DownloadStatus:
    DOWNLOADED = "downloaded"
    SKIPPED = "skipped"
    FAILED = "failed"


def download_attachment(
    attachment_index: int,
    attachment_url: str,
    channel_id: str,
    message_id: str,
    output_path: str,
) -> str:
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

    try:
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
    except Exception as e:
        console.print(f"[red]Error downloading file: {str(e)}[/]")
        return DownloadStatus.FAILED
