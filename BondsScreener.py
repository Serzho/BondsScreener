from cfg import TOKEN
from core.BrokerClient import TinkoffClient
from core.TableClient import GoogleSheetsClient
from core.TableExporter import TableExporter


def main():
    tinkoff_client = TinkoffClient(token=TOKEN)
    google_sheets_client = GoogleSheetsClient()
    table_exporter = TableExporter()

    # google_sheets_client.write_flb([])
    tinkoff_client.update_bonds_storage()
    # flb_table = table_exporter.get_table(tinkoff_client.get_flb())
    print(tinkoff_client.get_ru_corp())
    ru_corp_table = table_exporter.get_table(tinkoff_client.get_ru_corp())
    # google_sheets_client.write_flb(flb_table)
    google_sheets_client.write_ru_corp(ru_corp_table)


if __name__ == "__main__":
    main()
