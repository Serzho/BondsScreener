from abc import ABC, abstractmethod
from datetime import timedelta

from tinkoff.invest import Client, CandleInterval
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
        with self.__client_cls(self.__token, target=INVEST_GRPC_API) as client:
            bonds = client.instruments.bonds()
            flb_storage = self._bonds_storage['ru_flb']
            if bonds is not None:
                for bond in bonds.instruments:
                    if not bond.for_qual_investor_flag:
                        if bond.currency == 'rub':
                            if bond.sector == "government":
                                flb_storage.append({"ticker": bond.ticker,
                                                    "name": bond.name,
                                                    "aci": bond.aci_value,
                                                    "currency": bond.currency,
                                                    "placement_date": bond.placement_date.date(),
                                                    "maturity_date": bond.maturity_date.date(),
                                                    #"coupon_rate": client.,
                                                    "nominal_value": bond.nominal.units,
                                                    #"real_value": ,
                                                    "coupon_quantity_per_year": bond.coupon_quantity_per_year
                                })




