import datetime
from abc import ABC, abstractmethod
from datetime import timedelta

import tinkoff.invest
from tinkoff.invest import Client, CandleInterval, MoneyValue
from tinkoff.invest.constants import INVEST_GRPC_API
from tinkoff.invest.utils import now


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

    def set_token(self, token: str = ""):
        self.__token = token

    @property
    def token(self):
        return self.__token

    def get_bonds(self):
        return self._bonds_storage

    def update_bonds_storage(self):
        def handle_coupons(response: tinkoff.invest.GetBondCouponsResponse) -> list[dict]:
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

        with self.__client_cls(self.__token, target=INVEST_GRPC_API) as client:
            bonds = client.instruments.bonds()
            flb_storage = self._bonds_storage['ru_flb']
            if bonds is not None:
                for bond in bonds.instruments:
                    if not bond.for_qual_investor_flag and not bond.floating_coupon_flag:
                        if bond.currency == 'rub':
                            if bond.sector == "government":
                                flb_storage.append({"ticker": bond.ticker,
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
                                                    "coupon_quantity_per_year": bond.coupon_quantity_per_year
                                })




