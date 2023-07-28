import datetime
import logging
import time
from abc import ABC, abstractmethod
import gspread
from gspread import Client, Spreadsheet, Worksheet

from cfg import EMAIL, TABLE_TOKEN_FILE
from gspread_formatting import BooleanCondition, DataValidationRule, set_data_validation_for_cell_range, set_column_widths


FORMAT_DICT = {
    "MAIN": {'cols_width': {
        'B': 200, 'C': 240
    }},
    "FLB": {'cols_width': {
        'A': 120, 'B': 220, 'C': 60, 'D': 110, 'E': 135, 'F': 120, 'G': 160, 'H': 180, 'I': 80, 'J': 105, 'K': 145, 'L': 175
    }},
    "FLC": {'cols_width': {
        'A': 120, 'B': 220, 'C': 60, 'D': 110, 'E': 135, 'F': 120, 'G': 160, 'H': 180, 'I': 80, 'J': 105, 'K': 145, 'L': 175
    }},
    "SPECIAL": {'cols_width': {
        'A': 120, 'B': 220, 'C': 140, 'D': 60, 'E': 110, 'F': 135, 'G': 120, 'H': 160, 'I': 180, 'J': 80, 'K': 105, 'L': 145, 'M': 175
    }},
    "RU_CORP": {'cols_width': {
        'A': 120, 'B': 220, 'C': 60, 'D': 110, 'E': 135, 'F': 120, 'G': 160, 'H': 180, 'I': 80, 'J': 105, 'K': 145, 'L': 175
    }}
}


class TableClient(ABC):
    __slots__ = ["_sheet"]

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def _connect_table(self, *args, **kwargs):
        pass

    @abstractmethod
    def _fill_main_sheet(self, *args, **kwargs):
        pass

    @abstractmethod
    def set_status(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_update_flag(self, *args, **kwargs):
        pass

    @abstractmethod
    def write_flb(self, *args, **kwargs):
        pass

    @abstractmethod
    def write_fcb(self, *args, **kwargs):
        pass

    @abstractmethod
    def _write_table(self, *args, **kwargs):
        pass

    @abstractmethod
    def write_ru_corp(self, *args, **kwargs):
        pass

    @abstractmethod
    def format_sheets(self, *args, **kwargs):
        pass


class GoogleSheetsClient(TableClient):
    def __init__(self):
        logging.info("Initializing google sheets client...")
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        gs_client = gspread.service_account(filename=TABLE_TOKEN_FILE, scopes=scopes)
        self._sheet: Spreadsheet
        self._worksheets = {"FLB": None, "RU_CORP": None, "MAIN": None, "FCB": None, "SPECIAL": None}
        logging.info("Connecting table...")
        self._connect_table(gs_client, "Bonds")
        self._fill_main_sheet()
        self.format_sheets()
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

    def set_status(self, status: str = "updating", bonds_count: int = 0):
        logging.info(f"Setting status '{status}'")
        worksheet: Worksheet | None
        worksheet = self._worksheets.get("MAIN")
        today = datetime.datetime.today().strftime("%d-%m-%y %H:%M")
        if status == "updating":
            worksheet.batch_update([
                {'range': "B5:C8", 'values': [
                    ['Последнее обновление:', '-'], ['Количество облигаций в базе:', '-'],
                    ['Обновить:', False], ['Статус таблицы:', 'ОБНОВЛЕНИЕ...']]
                 }
            ])
        elif status == "updated":
            worksheet.batch_update([
                {'range': "B5:C8", 'values': [
                    ['Последнее обновление:', f'{today}'], ['Количество облигаций в базе:', f'{bonds_count}'],
                    ['Обновить:', False], ['Статус таблицы:', 'Готово']]
                 }
            ])
        else:
            logging.error(f"UNEXPECTED STATUS: '{status}'")
        logging.info("Status was updated")

    def get_update_flag(self) -> bool:
        worksheet: Worksheet | None
        worksheet = self._worksheets.get("MAIN")
        try:
            result = worksheet.acell('C7').value == 'TRUE'
        except gspread.exceptions.APIError as e:
            print("GSPREAD RESOURCE EXHAUSTED")
            logging.warning("Gspread resource exhausted! Waiting 1 sec")
            logging.exception(e)
            time.sleep(1)
            result = self.get_update_flag()
        except Exception as e:
            print(f"UNEXPECTED EXCEPTION: {e}")
            logging.critical(f"UNEXPECTED EXCEPTION IN GSPREAD: {e}")
            logging.exception(e)
            return False
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

    def _write_table(self, values_list: list, start_cell: tuple[int, int], worksheet: Worksheet | None,
                     unique_header: list = None):
        self.format_sheets()
        if worksheet is None:
            return

        logging.info(f"Writing table: values_amount={len(values_list)}, start_cell={start_cell}, "
                     f"worksheet={worksheet.title}, unique_header={unique_header}")

        header_list = [
            'Тикер', 'Название', 'Валюта', 'Уровень риска', 'Дата размещения',
            'Дата погашения', 'Времени до погашения', 'Количество купонов в год',
            'Цена (rub)', 'Номинал (rub)', 'Простая доходность', 'Эффективная доходность'
        ] if unique_header is None else unique_header

        header_range = (
            chr(ord('A') + start_cell[0] - 1), start_cell[1],
            chr(ord('A') + start_cell[0] - 1 + len(header_list)), start_cell[1]
        )

        instrument_range = header_range[0], header_range[1] + 1, header_range[2], header_range[3] + 1 + len(values_list)

        logging.info(f"Header_range={header_range}, Instrument_range={instrument_range}")
        worksheet.batch_update([
            {'range': "{}{}:{}{}".format(*header_range), 'values': [header_list]},
            {'range': "{}{}:{}{}".format(*instrument_range), 'values': values_list}
        ])
        logging.info("Table was writed")

    def format_sheets(self):
        logging.info("Formatting worksheets")
        for ws_title, format_dict in FORMAT_DICT.items():
            worksheet = self._worksheets.get(ws_title)
            if worksheet is None:
                logging.error(f"UNEXPECTED WORKSHEET TITLE={ws_title}")
                continue
            cols_list = [tuple(col) for col in format_dict['cols_width'].items()]
            set_column_widths(worksheet, cols_list)
            logging.info(f"{ws_title} was formatted")

    def write_flb(self, flb_list: list[list], start_cell=(1, 1)):
        logging.info("Writing flb table")
        worksheet = self._worksheets.get("FLB")
        self._write_table(flb_list, start_cell, worksheet)

    def write_ru_corp(self, ru_corp_list: list[list], start_cell=(1, 1)):
        logging.info("Writing russian corporate bonds table")
        worksheet = self._worksheets.get("RU_CORP")
        self._write_table(ru_corp_list, start_cell, worksheet)

    def write_fcb(self, fcb_list: list[list], start_cell=(1, 1)):
        logging.info("Writing fcb table")
        worksheet = self._worksheets.get("FCB")
        self._write_table(fcb_list, start_cell, worksheet)

    def write_special(self, special_list: list[list], start_cell=(1, 1)):
        logging.info("Writing special table")
        worksheet = self._worksheets.get("SPECIAL")
        header = [
            'Тикер', 'Название', 'Особенность', 'Валюта', 'Уровень риска', 'Дата размещения',
            'Дата погашения', 'Времени до погашения', 'Количество купонов в год',
            'Цена (rub)', 'Номинал (rub)', 'Простая доходность', 'Эффективная доходность'
        ]
        self._write_table(special_list, start_cell, worksheet, header)
