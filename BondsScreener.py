from cfg import TOKEN
from core.BrokerClient import TinkoffClient


def main():
    tinkoff_client = TinkoffClient(token=TOKEN)
    tinkoff_client.update_bonds_storage()
    print(tinkoff_client.get_bonds())


if __name__ == "__main__":
    main()
