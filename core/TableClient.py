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
        gs_client = gspread.service_account(filename=TABLE_TOKEN_FILE)
        self._sheet: Spreadsheet
        self._connect_table(gs_client, "Bonds")

    def _connect_table(self, gs_client: Client, table_title: str):
        if table_title not in [sheet.title for sheet in gs_client.openall()]:
            gs_client.create(table_title)
            self._sheet = gs_client.open(table_title)
            self._sheet.add_worksheet(title="Main", rows=100, cols=20)
        else:
            self._sheet = gs_client.open(table_title)
        self._sheet.share(EMAIL, perm_type='user', role='writer')

    def write_flb(self, flb_list: list[tuple]):
        worksheet = self._sheet.worksheet("Main")
        worksheet.update("A1:J1", ['Тикер', 'Название', 'Валюта', 'Дата размещения',
                                   'Дата погашения', 'Времени до погашения', 'Количество купонов в год',
                                   'Цена', 'Номинал', 'Реальная доходность'])
        for row_ind, fld_tuple in enumerate(flb_list):
            for col_ind in range(1, 11):
                worksheet.update(row_ind + 2, col_ind, fld_tuple[col_ind])





