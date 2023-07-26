import datetime
import logging
from abc import ABC, abstractmethod
import gspread
from gspread import Client, Spreadsheet, Worksheet

from cfg import EMAIL, TABLE_TOKEN_FILE
from gspread_formatting import BooleanCondition, DataValidationRule, set_data_validation_for_cell_range


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
        logging.info("Initializing google sheets client...")
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        gs_client = gspread.service_account(filename=TABLE_TOKEN_FILE, scopes=scopes)
        self._sheet: Spreadsheet
        self._worksheets = {"FLB": None, "RU_CORP": None, "MAIN": None}
        logging.info("Connecting table...")
        self._connect_table(gs_client, "Bonds")
        self._fill_main_sheet()
        print(self._sheet.url)
        logging.info(f"Google sheet client was successfully initialized! URL={self._sheet.url}")

    def _fill_main_sheet(self):
        logging.info("Filling main page")
        worksheet: Worksheet | None
        worksheet = self._worksheets.get("MAIN")
        assert type(worksheet) == Worksheet
        worksheet.batch_update([
            {'range': "B4:C12", 'values': [
                ['ТАБЛИЦА ОБЛИГАЦИЙ', ''], ['Последнее обновление:', '01-01-1970 00:00'],
                ['Количество облигаций в базе:', '0'], ['Обновить:', False], ['Статус таблицы:', 'Не определен'],
                ['ТАБЛИЦА СОЗДАНА ПРЕКРАСНЫМ МНОЙ', ''], ['telegram', '@serzho_christ'], ['github', '@serzho'],
                ['linkedin', 'http://www.linkedin.com/in/serzhochrist/']]
             }
        ])
        validation_rule = DataValidationRule(
            BooleanCondition('BOOLEAN', []),
            showCustomUi=True
        )
        set_data_validation_for_cell_range(worksheet, 'C7', validation_rule)
        logging.info("Main page was filled")

    def set_updating_status(self):
        logging.info("Setting status 'updating'")
        worksheet: Worksheet | None
        worksheet = self._worksheets.get("MAIN")
        worksheet.batch_update([
            {'range': "B5:C8", 'values': [
                ['Последнее обновление:', '-'], ['Количество облигаций в базе:', '-'],
                ['Обновить:', False], ['Статус таблицы:', 'ОБНОВЛЕНИЕ...']]
             }
        ])
        logging.info("Status was updated")

    def set_updated_status(self, bonds_count: int = 0):
        logging.info("Setting status 'updated'")
        worksheet: Worksheet | None
        worksheet = self._worksheets.get("MAIN")
        today = datetime.datetime.today().strftime("%d-%m-%y %H:%M")
        worksheet.batch_update([
            {'range': "B5:C8", 'values': [
                ['Последнее обновление:', f'{today}'], ['Количество облигаций в базе:', f'{bonds_count}'],
                ['Обновить:', False], ['Статус таблицы:', 'Готово']]
             }
        ])
        logging.info("Status was updated")

    def get_update_flag(self) -> bool:
        worksheet: Worksheet | None
        worksheet = self._worksheets.get("MAIN")
        result = worksheet.acell('C7').value == 'TRUE'
        logging.info(f"Update flag = {result}")
        return result

    def _connect_table(self, gs_client: Client, table_title: str):
        logging.info("Connecting to table")
        if table_title not in [sheet.title for sheet in gs_client.openall()]:
            gs_client.create(table_title)
            logging.info(f"Table {table_title} was created")

        self._sheet = gs_client.open(table_title)
        for worksheet_title in self._worksheets.keys():
            if worksheet_title not in [ws.title for ws in self._sheet.worksheets()]:
                self._sheet.add_worksheet(worksheet_title, rows=10000, cols=100)
                logging.info(f"Sheet {worksheet_title} was created")
            self._worksheets.update({worksheet_title: self._sheet.worksheet(worksheet_title)})

        self._sheet.share(EMAIL, perm_type='user', role='writer')
        logging.info("Successfully connected to table")

    @staticmethod
    def _write_table(values_list: list, start_cell: tuple[int, int], worksheet: Worksheet | None):

        if worksheet is None:
            return

        logging.info(f"Writing table: values_amount={len(values_list)}, start_cell={start_cell}, "
                     f"worksheet={worksheet.title}")

        header_list = [
            'Тикер', 'Название', 'Валюта', 'Уровень риска', 'Дата размещения',
            'Дата погашения', 'Времени до погашения', 'Количество купонов в год',
            'Цена', 'Номинал', 'Простая доходность', 'Эффективная доходность'
        ]

        header_range = chr(ord('A') + start_cell[0] - 1), start_cell[1], \
                       chr(ord('A') + start_cell[0] - 1 + len(header_list)), start_cell[1]
        instrument_range = header_range[0], header_range[1] + 1, header_range[2], header_range[3] + 1 + len(values_list)

        logging.info(f"Header_range={header_range}, Instrument_range={instrument_range}")
        worksheet.batch_update([
            {'range': "{}{}:{}{}".format(*header_range), 'values': [header_list]},
            {'range': "{}{}:{}{}".format(*instrument_range), 'values': values_list}
        ])
        logging.info("Table was writed")

    def write_flb(self, flb_list: list[list], start_cell=(1, 1)):
        logging.info("Writing flb table")
        worksheet = self._worksheets.get("FLB")
        self._write_table(flb_list, start_cell, worksheet)

    def write_ru_corp(self, ru_corp_list: list[list], start_cell=(1, 1)):
        logging.info("Writing russian corporate bonds table")
        worksheet = self._worksheets.get("RU_CORP")
        self._write_table(ru_corp_list, start_cell, worksheet)
