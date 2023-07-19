import datetime
from cfg import COMMISSION


class TableExporter:
    def __init__(self):
        pass

    @staticmethod
    def _date_dt(first_date: datetime.date, second_date: datetime.date) -> (int, int):
        dt = second_date - first_date
        years = dt.days // 365
        months = (dt.days % 365) // 30
        if years == 0 and months == 0:
            months = 1
        return years, months

    @staticmethod
    def _prepare_date_dt(years: int, months: int) -> str:
        out = ""
        if years == 1:
            out += "1 год "
        elif 1 < years % 10 < 5 and not (1 < years // 10 < 2):
            out += f"{years} года "
        elif years != 0:
            out += f"{years} лет "
        if months == 1:
            out += "1 месяц"
        elif 1 < months < 5:
            out += f"{months} месяца"
        else:
            out += f"{months} месяцев"
        return out

    @staticmethod
    def _count_annual_profitability(date_dt: (int, int), coupons: list[dict], nominal_price: float, real_price: float,
                                    aci: float, currency: str) -> float:
        if currency != "rub":
            return 0.

        years, months = date_dt
        expenses = real_price + real_price * COMMISSION + aci
        total_coupons = 0
        today = datetime.date.today()

        for coupon in coupons:
            if today > coupon.get("date"):
                continue
            total_coupons += coupon.get("value") * 0.87

        repayment = nominal_price
        if nominal_price > real_price:
            repayment -= (nominal_price - real_price) * 0.13

        proceeds = repayment + total_coupons
        total_profit = proceeds / expenses
        return round(100 * total_profit ** (12 / (years * 12 + months)) - 100, 2)

    def _get_row_list(self, bond_dict: dict) -> list:
        date_diff = self._date_dt(datetime.date.today(), bond_dict.get("maturity_date"))
        annual_profit = self._count_annual_profitability(
            date_diff, bond_dict.get("coupons"), bond_dict.get("nominal_value"), bond_dict.get("real_value"),
            bond_dict.get("aci"), bond_dict.get("currency")
        )
        return [
            bond_dict.get("ticker"), bond_dict.get("name"), bond_dict.get("currency"),
            bond_dict.get("placement_date").strftime("%d-%m-%Y"), bond_dict.get("maturity_date").strftime("%d-%m-%Y"),
            self._prepare_date_dt(*date_diff), bond_dict.get("coupon_quantity_per_year"), bond_dict.get("real_value"),
            bond_dict.get("nominal_value"), annual_profit
        ]

    def get_table(self, bond_list: list[dict]) -> list[list]:
        return [self._get_row_list(bond_dict) for bond_dict in bond_list]
