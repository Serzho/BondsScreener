from abc import ABC, abstractmethod
import httplib2
import apiclient.discovery
from oauth2client.service_account import ServiceAccountCredentials
from cfg import EMAIL

TABLE_TOKEN_FILE = "table_token.json"

class TableClient(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def create_table(self):
        pass


class GoogleSheetsClient(TableClient):
    def __init__(self):
        credentials = ServiceAccountCredentials.from_json_keyfile_name(TABLE_TOKEN_FILE,
                                                                       ['https://www.googleapis.com/auth/spreadsheets',
                                                                        'https://www.googleapis.com/auth/drive'])
        http_auth = credentials.authorize(httplib2.Http())
        service = apiclient.discovery.build('sheets', 'v4', http=http_auth)
        print(service.spreadsheets())
        spreadsheet = service.spreadsheets().create(body={
            'properties': {'title': 'Первый тестовый документ', 'locale': 'ru_RU'},
            'sheets': [{'properties': {'sheetType': 'GRID',
                                       'sheetId': 0,
                                       'title': 'Лист номер один',
                                       'gridProperties': {'rowCount': 100, 'columnCount': 15}}}]
        }).execute()
        spreadsheet_id = spreadsheet['spreadsheetId']  # сохраняем идентификатор файла
        drive_service = apiclient.discovery.build('drive', 'v3', http=http_auth)

        access = drive_service.permissions().create(
            fileId=spreadsheet_id,
            body={'type': 'user', 'role': 'writer', 'emailAddress': EMAIL},
            # Открываем доступ на редактирование
            fields='id'
        ).execute()
        print('https://docs.google.com/spreadsheets/d/' + spreadsheet_id)

    def create_table(self):
        pass
