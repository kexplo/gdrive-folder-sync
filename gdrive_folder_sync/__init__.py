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


if __name__ == "__main__":
    cli()
