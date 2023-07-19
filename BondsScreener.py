from cfg import TOKEN
from core.BrokerClient import TinkoffClient
from core.TableClient import GoogleSheetsClient
from core.TableExporter import TableExporter


def main():
    tinkoff_client = TinkoffClient(token=TOKEN)
    google_sheets_client = GoogleSheetsClient()
    table_exporter = TableExporter()

    google_sheets_client.write_flb([])
    tinkoff_client.update_bonds_storage()
    flb_table = table_exporter.get_table(tinkoff_client.get_bonds().get("ru_flb"))
    google_sheets_client.write_flb(flb_table)


if __name__ == "__main__":
    main()
