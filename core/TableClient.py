from abc import ABC, abstractmethod
import gspread
from gspread import Client, Spreadsheet, Worksheet

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
        self._worksheets = {"FLB": None, "RU_CORP": None}
        print(self._sheet.url)

    def _connect_table(self, gs_client: Client, table_title: str):
        if table_title not in [sheet.title for sheet in gs_client.openall()]:
            gs_client.create(table_title)

        self._sheet = gs_client.open(table_title)
        for worksheet_title, worksheet in self._worksheets.items():
            if worksheet_title not in [ws.title for ws in self._sheet.worksheets()]:
                self._sheet.add_worksheet(worksheet_title, rows=100000, cols=1000)
            self._worksheets.update({worksheet_title: self._sheet.worksheet(worksheet_title)})

        self._sheet.share(EMAIL, perm_type='user', role='writer')

    @staticmethod
    def _write_table(values_list: list, header_list: list, start_cell: tuple[int, int], worksheet: Worksheet | None):
        if worksheet is None:
            return

        header_range = chr(ord('A') + start_cell[0] - 1), start_cell[1], \
                       chr(ord('A') + start_cell[0] - 1 + len(header_list)), start_cell[1]

        instrument_range = header_range[0], header_range[1] + 1, header_range[2], header_range[3] + 1 + len(values_list)
        worksheet.batch_update([
            {'range': "{}{}:{}{}".format(*header_range), 'values': [header_list]},
            {'range': "{}{}:{}{}".format(*instrument_range), 'values': values_list}
        ])

    def write_flb(self, flb_list: list[list], start_cell=(1, 1)):
        header_list = [
            'Тикер', 'Название', 'Валюта', 'Дата размещения',
            'Дата погашения', 'Времени до погашения', 'Количество купонов в год',
            'Цена', 'Номинал', 'Реальная доходность'
        ]
        worksheet = self._worksheets.get("FLB")
        self._write_table(flb_list, header_list, start_cell, worksheet)

    def write_ru_corp(self, ru_corp_list: list[list], start_cell=(1, 1)):
        header_list = [
            'Тикер', 'Название', 'Валюта', 'Дата размещения',
            'Дата погашения', 'Времени до погашения', 'Количество купонов в год',
            'Цена', 'Номинал', 'Реальная доходность'
        ]
        worksheet = self._worksheets.get("RU_CORP")
        self._write_table(ru_corp_list, header_list, start_cell, worksheet)
