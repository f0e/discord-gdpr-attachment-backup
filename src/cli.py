import click

from .commands.download_attachments import download_attachments
from .commands.date_cutoff import date_cutoff


@click.group()
def cli():
    """Discord GDPR data tools"""
    pass


# Register commands
cli.add_command(download_attachments)
cli.add_command(date_cutoff)


if __name__ == "__main__":
    cli()