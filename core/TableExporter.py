import datetime
import logging

from cfg import BOND_COMMISSION, CURRENCY_COMMISSION


class TableExporter:
    def __init__(self):
        logging.info("Table exporter was successfully initialized")

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
        elif 1 < years % 10 < 5 and not (1 == years // 10):
            out += f"{years} года "
        elif years != 0:
            out += f"{years} лет "
        if months == 1:
            out += "1 месяц"
        elif 1 < months < 5:
            out += f"{months} месяца"
        elif months != 0:
            out += f"{months} месяцев"
        return out

    @staticmethod
    def _count_proceeds_and_expenses(today: datetime.date, coupons: list[dict], nominal_price: float, real_price: float,
                                     aci: float) -> (float, float):
        logging.info(f"Counting proceeds and expenses: date={today}, coupons_amount={len(coupons)}, "
                     f"nominal_price={nominal_price}, real_price={real_price}, aci={aci}")
        expenses = (real_price + real_price * BOND_COMMISSION + aci)
        total_coupons = 0

        for coupon in coupons:
            if today >= coupon.get("date"):
                continue
            total_coupons += coupon.get("value") * 0.87

        repayment = nominal_price
        if nominal_price > real_price:
            repayment -= (nominal_price - real_price) * 0.13

        proceeds = repayment + total_coupons
        logging.info(f"Result of counting: proceeds={proceeds}, expenses={expenses}")
        return proceeds, expenses

    def _count_simple_profitability(self, date_dt: (int, int), coupons: list[dict], nominal_price: float,
                                    real_price: float, aci: float, currency: str) -> float:
        logging.info(f"Counting simple profitability: date={date_dt}, coupons_amount={len(coupons)}, "
                     f"nominal_price={nominal_price}, real_price={real_price}, aci={aci}, currency={currency}")
        years, months = date_dt
        today = datetime.date.today()
        proceeds, expenses = self._count_proceeds_and_expenses(today, coupons, nominal_price, real_price, aci)

        if expenses == 0.:
            logging.warning("Bond was not available to buying!")
            return 0.

        if currency != "rub":
            proceeds -= proceeds * CURRENCY_COMMISSION
            expenses += expenses * CURRENCY_COMMISSION

        total_profit = proceeds / expenses
        logging.info(f"Bond profit: total_profit={total_profit}, "
                     f"result={round(100 * total_profit ** (12 / (years * 12 + months)) - 100, 2)}")

        return round(100 * total_profit ** (12 / (years * 12 + months)) - 100, 2)

    def _count_effective_profitability(self, date_dt: (int, int), coupons: list[dict], nominal_price: float,
                                       real_price: float, aci: float, currency: str) -> float:
        logging.info(f"Counting effective profitability: date={date_dt}, coupons_amount={len(coupons)}, "
                     f"nominal_price={nominal_price}, real_price={real_price}, aci={aci}, currency={currency}")
        years, months = date_dt
        today = datetime.date.today()
        proceeds, expenses = self._count_proceeds_and_expenses(today, coupons, nominal_price, real_price, aci)
        today = datetime.date.today()

        if expenses == 0.:
            logging.warning("Bond was not available to buying!")
            return 0.

        logging.info("Counting re-investing coupons")
        for coupon in coupons:
            if today >= coupon.get("date"):
                continue
            coupon_proceeds, coupon_expenses = self._count_proceeds_and_expenses(
                coupon.get("date"), coupons, nominal_price, real_price, 0
            )
            scale = (0.87 * coupon.get("value")) / coupon_expenses
            proceeds += scale * coupon_proceeds - coupon.get("value") * 0.87
            logging.info(f"Coupon profit: proceeds={coupon_proceeds}, expenses={coupon_expenses}")

        if currency != "rub":
            proceeds -= proceeds * CURRENCY_COMMISSION
            expenses += expenses * CURRENCY_COMMISSION

        total_profit = proceeds / expenses

        logging.info(f"Bond profit: total_profit={total_profit}, "
                     f"result={round(100 * total_profit ** (12 / (years * 12 + months)) - 100, 2)}")

        return round(100 * total_profit ** (12 / (years * 12 + months)) - 100, 2)

    def _get_row_list(self, bond_dict: dict) -> list:
        logging.info(f"Getting row list for {bond_dict.get('ticker')}")
        date_diff = self._date_dt(datetime.date.today(), bond_dict.get("maturity_date"))
        exchange_rate = bond_dict.get("exchange_rate")
        simple_profit = self._count_simple_profitability(
            date_diff, bond_dict.get("coupons"), bond_dict.get("nominal_value"), bond_dict.get("real_value"),
            bond_dict.get("aci"), bond_dict.get("currency")
        )
        effective_profit = self._count_effective_profitability(
            date_diff, bond_dict.get("coupons"), bond_dict.get("nominal_value"), bond_dict.get("real_value"),
            bond_dict.get("aci"), bond_dict.get("currency")
        )

        row_list = [
            bond_dict.get("ticker"), bond_dict.get("name"), bond_dict.get("currency"), bond_dict.get("risk_level"),
            bond_dict.get("placement_date").strftime("%d-%m-%Y"), bond_dict.get("maturity_date").strftime("%d-%m-%Y"),
            self._prepare_date_dt(*date_diff), bond_dict.get("coupon_quantity_per_year"),
            bond_dict.get("real_value") * exchange_rate, bond_dict.get("nominal_value") * exchange_rate,
            simple_profit, effective_profit
        ]

        logging.info(f"Returning row list={row_list}")
        return row_list

    def get_table(self, bond_list: list[dict]) -> list[list]:
        logging.info(f"Getting bond table: bonds_amount={len(bond_list)}")
        table = []
        for bond_dict in bond_list:
            if bond_dict.get("nominal_value") == 0 or bond_dict.get("real_value") == 0 or bond_dict == {}:
                logging.warning(f"Not available bond: ticker={bond_dict.get('ticker')}")
                continue
            logging.info(f"Available bond: ticker={bond_dict.get('ticker')}")
            table.append(self._get_row_list(bond_dict))

        logging.info(f"Returning bond table: row_amount={len(table)}")
        return table
