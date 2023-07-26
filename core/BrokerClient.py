import datetime
import logging
import time
from abc import ABC, abstractmethod
from datetime import timedelta

import tinkoff.invest
from tinkoff.invest import Client, CandleInterval, MoneyValue, Bond
from tinkoff.invest.constants import INVEST_GRPC_API
from tinkoff.invest.utils import now
from cfg import UNARY_REQUEST_LIMIT, MAX_REQUEST_ATTEMPTS


request_delay = 0.85 * 60 / UNARY_REQUEST_LIMIT


class BrokerClient(ABC):
    __slots__ = ["__client_cls", "_bonds_storage", "__token"]

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def get_bonds(self):
        pass

    @abstractmethod
    def update_bonds_storage(self):
        pass

    @abstractmethod
    def set_token(self, token: str = ""):
        pass

    @abstractmethod
    def token(self):
        pass


class TinkoffClient(BrokerClient):
    def __init__(self, token: str = ""):
        self.__client_cls = Client
        self._bonds_storage = {"ru_flb": [], "ru_corp": []}
        self.__token = token
        logging.info("Broker client was initialized")

    def set_token(self, token: str = ""):
        self.__token = token

    @property
    def token(self):
        return self.__token

    def get_bonds(self):
        return self._bonds_storage

    def get_flb(self):
        return self._bonds_storage["ru_flb"]

    def get_ru_corp(self):
        return self._bonds_storage['ru_corp']

    def update_bonds_storage(self):
        def handle_coupons(response: tinkoff.invest.GetBondCouponsResponse) -> list[dict]:
            logging.info(f"Handling coupons: coupons_amount={len(response.events)}")
            out = []
            for event in response.events:
                out.append({
                    "number": event.coupon_number,
                    "date": event.coupon_date.date(),
                    "value": handle_price(event.pay_one_bond)
                })
            return out

        def handle_price(price_entity: MoneyValue) -> float:
            units, nano = price_entity.units, price_entity.nano
            return units + nano / 1000000000

        def get_bond_dict(bond: Bond, attempts: int = 1) -> dict:
            logging.info(f"Getting bond list: ticker={bond.ticker}")
            try:
                if handle_price(bond.nominal) == 0.0:
                    logging.warning(f"Not available bond: ticker={bond.ticker}")
                    return {}
                time.sleep(request_delay)
                out_dict = {
                    "ticker": bond.ticker,
                    "name": bond.name,
                    "aci": handle_price(bond.aci_value),
                    "currency": bond.currency,
                    "placement_date": bond.placement_date.date(),
                    "maturity_date": bond.maturity_date.date(),
                    "coupons": handle_coupons(client.instruments.get_bond_coupons(
                        figi=bond.figi, to=bond.maturity_date
                    )),
                    "nominal_value": handle_price(bond.nominal),
                    "real_value": handle_price(client.market_data.get_last_prices(
                        figi=[bond.figi]
                    ).last_prices[0].price) * 0.01 * handle_price(bond.nominal),
                    "coupon_quantity_per_year": bond.coupon_quantity_per_year,
                    "risk_level": bond.risk_level
                }
                logging.info(f"Bond_dict={out_dict}")
                return out_dict

            except tinkoff.invest.exceptions.RequestError:
                logging.warning("Resource exhausted warning! Waiting 0.5 seconds")
                print("RESOURCE_EXHAUSTED...")
                time.sleep(0.5)
                if attempts > MAX_REQUEST_ATTEMPTS:
                    logging.error(f"MAX_REQUEST_ATTEMPTS_ERROR: {bond.ticker}")
                    print(f"Skipping bond {bond.ticker}")
                    return {}
                logging.warning(f"Retrying getting bond dict: {bond.ticker}")
                return get_bond_dict(bond, attempts + 1)
            except Exception as e:
                logging.critical(f"UNEXPECTED ERROR!!! {e}")
                print(e)
                return {}

        logging.info("Updating bonds storage...")
        with self.__client_cls(self.__token, target=INVEST_GRPC_API) as client:
            bonds = client.instruments.bonds()
            flb_storage = self._bonds_storage['ru_flb']
            bonds_count = len(bonds.instruments)
            ru_corp_storage = self._bonds_storage['ru_corp']
            logging.info(f"Bonds amount = {bonds_count}")
            print(f"Count of bonds: {bonds_count}")
            if bonds is not None:
                for number, bond in enumerate(bonds.instruments):
                    if number % 10 == 0:
                        print(f"{round(100 * number / bonds_count, 2)}")
                    if not any([bond.for_qual_investor_flag, bond.floating_coupon_flag, bond.amortization_flag]):
                        if bond.currency == 'rub':
                            if bond.sector == "government":
                                logging.info(f"FLB Bond: {bond.ticker}")
                                flb_storage.append(get_bond_dict(bond))
                            else:
                                logging.info(f"RU CORP Bond: {bond.ticker}")
                                ru_corp_storage.append(get_bond_dict(bond))
                        else:
                            print(bond.ticker, bond.currency)
                    else:
                        logging.warning(f"Unsuitable bond: {bond.ticker}")
            else:
                logging.critical("BONDS_IS_NONE_ERROR")







