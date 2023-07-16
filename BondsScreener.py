from cfg import TOKEN
from core.BrokerClient import TinkoffClient
from core.TableClient import GoogleSheetsClient

def main():
    '''tinkoff_client = TinkoffClient(token=TOKEN)
    tinkoff_client.update_bonds_storage()
    print(tinkoff_client.get_bonds())'''
    google_sheets_client = GoogleSheetsClient()


if __name__ == "__main__":
    main()
