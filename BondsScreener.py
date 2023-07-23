import datetime
import time

from cfg import TOKEN
from core.BrokerClient import TinkoffClient
from core.TableClient import GoogleSheetsClient
from core.TableExporter import TableExporter


def main():
    tinkoff_client = TinkoffClient(token=TOKEN)
    google_sheets_client = GoogleSheetsClient()
    table_exporter = TableExporter()

    while True:
        time.sleep(1)
        if google_sheets_client.get_update_flag():
            google_sheets_client.set_updating_status()

            tinkoff_client.update_bonds_storage()

            flb_table = table_exporter.get_table(tinkoff_client.get_flb())
            ru_corp_table = table_exporter.get_table(tinkoff_client.get_ru_corp())

            google_sheets_client.write_flb(flb_table)
            google_sheets_client.write_ru_corp(ru_corp_table)
            google_sheets_client.set_updated_status(len(flb_table) + len(ru_corp_table))


if __name__ == "__main__":
    main()
    # ru_corp_table = table_exporter.get_table([
    #     {'ticker': 'RU000A101228', 'name': 'МОЭК выпуск 3', 'aci': 18.6, 'currency': 'rub', 'placement_date': datetime.date(2019, 11, 15), 'maturity_date': datetime.date(2025, 11, 7), 'coupons': [{'number': 2, 'date': datetime.date(2020, 11, 13), 'value': 33.91}, {'number': 3, 'date': datetime.date(2021, 5, 14), 'value': 33.91}, {'number': 4, 'date': datetime.date(2021, 11, 12), 'value': 33.91}, {'number': 5, 'date': datetime.date(2022, 5, 13), 'value': 33.91}, {'number': 6, 'date': datetime.date(2022, 11, 11), 'value': 33.91}, {'number': 7, 'date': datetime.date(2023, 5, 12), 'value': 46.37}, {'number': 8, 'date': datetime.date(2023, 11, 10), 'value': 46.37}, {'number': 9, 'date': datetime.date(2024, 5, 10), 'value': 46.37}, {'number': 10, 'date': datetime.date(2024, 11, 8), 'value': 46.37}, {'number': 11, 'date': datetime.date(2025, 5, 9), 'value': 0.0}, {'number': 12, 'date': datetime.date(2025, 11, 7), 'value': 0.0}], 'nominal_value': 1000.0, 'real_value': 1000.9999999999999, 'coupon_quantity_per_year': 2, 'risk_level': 2}])
    # print(tinkoff_client.get_ru_corp())

