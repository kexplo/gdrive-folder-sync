from typing import Optional

import click

from gdrive_folder_sync.gdrive import GDrive


@click.group()
def cli():
    pass


@cli.command(help="Sync between two folders")
@click.argument("src_folder_id")
@click.argument("dest_folder_id")
@click.option("--no-recursive", is_flag=True)
def sync(src_folder_id: str, dest_folder_id: str, no_recursive: bool):
    gdrive = GDrive()
    gdrive.sync(src_folder_id, dest_folder_id, not no_recursive)


@cli.command(help="Copy single file")
@click.argument("file_id")
@click.argument("dest_folder_id")
def copy(file_id: str, dest_folder_id: str):
    gdrive = GDrive()
    gdrive.copy_file_to_parent(file_id, dest_folder_id)


@cli.command(name="list", help="Listing files in the folder")
@click.argument("folder_id")
@click.option("-f", "--name-filter", type=click.STRING)
@click.option("--no-header", is_flag=True)
def list_cmd(folder_id: str, name_filter: Optional[str], no_header: bool):
    gdrive = GDrive()
    _, files = gdrive.get_folders_and_files(folder_id, name_filter)

    if not no_header:
        col_size = max(len(f['id']) for f in files)
        click.echo("{:<{col_size}}\tname".format('id', col_size=col_size))
    for file in files:
        click.echo(f"{file['id']}\t{file['name']}")


if __name__ == "__main__":
    cli()
