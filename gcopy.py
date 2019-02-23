# -*- coding: utf-8 -*-

from typing import Dict, List, Tuple

from apiclient.discovery import build
from httplib2 import Http
from oauth2client import client, file, tools

from typing import TYPE_CHECKING  # noqa
if TYPE_CHECKING:
    from typing import Any, Union  # noqa: F401


class GDrive(object):

    def __init__(self):
        # Setup the Drive v3 API
        # scopes = ['https://www.googleapis.com/auth/drive.metadata',
        #           'https://www.googleapis.com/auth/drive.file',
        #           ]
        scopes = ['https://www.googleapis.com/auth/drive']
        store = file.Storage('credentials.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('client_secret.json', scopes)
            creds = tools.run_flow(flow, store)
        self.service = build('drive', 'v3', http=creds.authorize(Http()))
        self.root_id = self.service.files().get(fileId='root').execute()['id']

    def get_folders_and_files(self, parent_id: str) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:  # noqa: E501
        all_items = []  # type: List[Dict[str, str]]
        next_page_token = None

        def f():
            nonlocal all_items
            nonlocal next_page_token
            results = self.service.files().list(
                pageSize=100, orderBy='folder',
                q='\'{}\' in parents'.format(parent_id),
                pageToken=next_page_token).execute()
            next_page_token = results.get('nextPageToken')
            items = results.get('files')
            if items:
                all_items += items
        f()
        while next_page_token is not None:
            f()

        folders = []  # type: List[Dict[str, str]]
        files = []  # type: List[Dict[str, str]]
        for item in all_items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                folders.append(item)
            else:
                files.append(item)

        def sort_func(k):
            return k['name']
        return sorted(folders, key=sort_func), sorted(files, key=sort_func)

    def file_in_parent(self, filename: str, parent_id: str) -> bool:
        _, files = self.get_folders_and_files(parent_id)
        filenames = [f['name'] for f in files]
        return filename in filenames

    def folder_in_parent(self, folder_name: str, parent_id: str, folders=None) -> bool:  # noqa: E501
        if folders is None:
            folders, _ = self.get_folders_and_files(parent_id)
        folder_names = [f['name'] for f in folders]
        return folder_name in folder_names

    def copy_file_to_parent(self, file_id: str, parent_id: str) -> None:
        self.service.files().copy(
            fileId=file_id, body={'parents': [parent_id]}).execute()

    def print_branch(self, name: str, level: int) -> None:
        print('{}├── {}'.format('│   ' * level, name))

    def tree(self, parent_ids: List[str], level: int=0) -> None:
        if level == 0:
            print('.')
        for pid in parent_ids:
            folders, files = self.get_folders_and_files(pid)
            for folder in folders:
                self.print_branch(folder['name'], level)
                self.tree([folder['id']], level+1)
            for _file in files:
                self.print_branch(_file['name'], level)

    def create_folder(self, folder_name: str, parent_id: str) -> Dict[str, str]:  # noqa: E501
        return self.service.files().create(body={
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id],
            'name': folder_name}).execute()

    def ensure_folder_id_by_name(self, folder_name: str, parent_id: str) -> str:  # noqa: E501
        folders, _ = self.get_folders_and_files(parent_id)
        if not self.folder_in_parent(folder_name, parent_id, folders=folders):
            return self.create_folder(folder_name, parent_id)['id']
        for folder in folders:
            if folder['name'] == folder_name:
                return folder['id']
        raise Exception('Can not ensure folder: {}'.format(folder_name))

    def sync(self, source_parent_id: str, target_parent_id: str, recursive=True) -> List[str]:  # noqa: E501
        print('syncing: {} -> {}'.format(source_parent_id, target_parent_id))

        copied_files = []  # type: List[str]

        source_folders, source_files = \
            self.get_folders_and_files(source_parent_id)

        if recursive:
            for source_folder in source_folders:
                print(' - ensure_folder:{} [ {} ]'.format(
                    source_folder['name'], source_folder['id']))
                target_folder_id = self.ensure_folder_id_by_name(
                    source_folder['name'],
                    target_parent_id)
                copied_files.extend(self.sync(source_folder['id'],
                                              target_folder_id))

        _, target_files = self.get_folders_and_files(target_parent_id)

        def file_in_target_files(filename: str) -> bool:
            for target_file in target_files:
                if target_file['name'] == filename:
                    return True
            return False

        for _file in source_files:
            if not file_in_target_files(_file['name']):
                print('   - copy file: {} [ {} ]'.format(_file['name'],
                                                         _file['id']))
                copied_files.append(_file['name'])
                self.copy_file_to_parent(_file['id'], target_parent_id)
            else:
                print('   - file exists: {}'.format(_file['name']))

        return copied_files

# gdrive = GDrive()
# copied_files = gdrive.sync(source_parent_id='..', target_parent_id='..',
#                            recursive=True)
