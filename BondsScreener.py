import logging
import time

from cfg import TOKEN, LOGGING_LEVEL, START_TYPE
from core.BrokerClient import TinkoffClient
from core.TableClient import GoogleSheetsClient
from core.TableExporter import TableExporter


def config_logging():
    if LOGGING_LEVEL == "INFO":
        level = logging.INFO
    elif LOGGING_LEVEL == "WARNING":
        level = logging.WARNING
    elif LOGGING_LEVEL == "ERROR":
        level = logging.ERROR
    elif LOGGING_LEVEL == "CRITICAL":
        level = logging.CRITICAL
    else:
        level = logging.DEBUG

    logging.basicConfig(level=level, filename="bs_log.log", filemode="a",
                        format="%(asctime)s | (%(filename)s).%(funcName)s: %(levelname)s - %(message)s")
    logging.info("Logging was successfully initialized")


def test():
    tinkoff_client = TinkoffClient(token=TOKEN)
    tinkoff_client.update_bonds_storage()


def main():
    tinkoff_client = TinkoffClient(token=TOKEN)
    google_sheets_client = GoogleSheetsClient()
    table_exporter = TableExporter()

    logging.info("Starting server...")
    while True:
        time.sleep(1)
        if google_sheets_client.get_update_flag():
            logging.info("Updating table")
            google_sheets_client.set_status("updating")

            logging.info("Updating bonds storage")
            tinkoff_client.update_bonds_storage()

            logging.info("Getting bonds table")
            flb_table = table_exporter.get_table(tinkoff_client.get_flb())
            ru_corp_table = table_exporter.get_table(tinkoff_client.get_ru_corp())
            fcb_table = table_exporter.get_table(tinkoff_client.get_fcb())
            special_table = table_exporter.get_table(tinkoff_client.get_special())

            logging.info("Writing bonds table to the google sheets")
            google_sheets_client.write_flb(flb_table)
            google_sheets_client.write_ru_corp(ru_corp_table)
            google_sheets_client.write_fcb(fcb_table)
            google_sheets_client.write_special(special_table)
            google_sheets_client.set_status("updated", len(flb_table) + len(ru_corp_table) + len(fcb_table))


if __name__ == "__main__":
    config_logging()
    if START_TYPE == "MAIN":
        logging.info("Starting at normal mode")
        main()
    elif START_TYPE == "TEST":
        logging.error("Starting at testing mode")
        test()


