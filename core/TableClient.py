from abc import ABC, abstractmethod
import gspread
from gspread import Client, Spreadsheet

from cfg import EMAIL, TABLE_TOKEN_FILE


class TableClient(ABC):
    __slots__ = ["_sheet"]

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def _connect_table(self, *args, **kwargs):
        pass

    @abstractmethod
    def write_flb(self, flb_list: list[tuple]):
        pass


class GoogleSheetsClient(TableClient):
    def __init__(self):
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        gs_client = gspread.service_account(filename=TABLE_TOKEN_FILE, scopes=scopes)
        self._sheet: Spreadsheet
        self._connect_table(gs_client, "Bonds")
        print(self._sheet.url)

    def _connect_table(self, gs_client: Client, table_title: str):
        if table_title not in [sheet.title for sheet in gs_client.openall()]:
            gs_client.create(table_title)
            self._sheet = gs_client.open(table_title)
            self._sheet.add_worksheet(title="Main", rows=100, cols=20)
        else:
            self._sheet = gs_client.open(table_title)
        self._sheet.share(EMAIL, perm_type='user', role='writer')

    def _write_table(self, values_list: list, header_list: list, start_cell: tuple[int, int]):
        header_range = chr(ord('A') + start_cell[1] - 1), \
                       start_cell[0], \
                       chr(ord('A') + start_cell[1] - 1 + len(header_list)), \
                       start_cell[0]
        worksheet = self._sheet.worksheet("Main")
        instrument_range = header_range[0], header_range[1] + 1, header_range[2], header_range[3] + 1 + len(values_list)
        worksheet.batch_update([
            {'range': "{}{}:{}{}".format(*header_range), 'values': [header_list]},
            {'range': "{}{}:{}{}".format(*instrument_range), 'values': values_list}
        ])

    def write_flb(self, flb_list: list[list], start_cell = (1, 1)):
        header_list = [
            'Тикер', 'Название', 'Валюта', 'Дата размещения',
            'Дата погашения', 'Времени до погашения', 'Количество купонов в год',
            'Цена', 'Номинал', 'Реальная доходность'
        ]
        # print(flb_list)
        self._write_table(flb_list, header_list, start_cell)




