from decimal import Decimal
from typing import TypeVar, Callable
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import QuerySet

from account.models import User
from device.common import set_ws_status
from payment.models import Payment
from tariff.models import TariffPlan, ServiceArchive


UserId = TypeVar("UserId", bound=int)


class CustomException(AssertionError):
    def __str__(self) -> None:
        return self.args[1]


NOT_ENOUGH_FUNDS = CustomException("NotEnoughFunds", "Недостаточно средств.")
COUNT_NOT_ZERO = CustomException("COUNT_NOT_ZERO", "Пополняемое средство не может быть нулем.")
TARIFF_IS_NULL = CustomException("TARIFF_IS_NULL", "Тариф не определен.")


class BaseMain:
    def __init__(self, user: User, payment_id: str = None) -> None:
        self.user = user
        if isinstance(self.user.balance, float):
            self.user.balance = Decimal(self.user.balance)
        if isinstance(self.user.tariff_plan.price, float):
            self.user.tariff_plan.price = Decimal(self.user.tariff_plan.price)
        self.now_datetime = timezone.now()
        self.payment_id = payment_id

    def add_balance(self, count: float) -> None:
        self.user.balance = Decimal(count) + Decimal(self.user.balance)
        QuerySet(Payment).create(
            user=self.user,
            quantity=Decimal(count),
            payment=self.payment_id
        )

    def activate(self) -> None:
        self.user.balance -= self.user.tariff_plan.price
        self.user.start_datetime_pp = self.now_datetime
        self.user.end_datetime_pp = self.now_datetime + {
            "day": relativedelta(days=1),
            "month": relativedelta(months=1),
            "quarter": relativedelta(months=3),
            "halfyear": relativedelta(months=6),
            "year": relativedelta(years=1),
        }[self.user.tariff_plan.unit_measurement]
        QuerySet(ServiceArchive).create(
            user=self.user,
            start_datetime_pp=self.user.start_datetime_pp,
            end_datetime_pp=self.user.end_datetime_pp,
            tariff_plan=self.user.tariff_plan
        )
        self.user.tariff_plan.archive = True
        # set_ws_status(self.user, True)
        self.user.ws_status = True

    def extend(self) -> None:
        self.user.balance -= self.user.tariff_plan.price
        self.user.end_datetime_pp += {
            "day": relativedelta(days=1),
            "month": relativedelta(months=1),
            "two month": relativedelta(months=2),
            "quarter": relativedelta(months=3),
            "halfyear": relativedelta(months=6),
            "year": relativedelta(years=1),
            "constant": relativedelta(years=100)
        }[self.user.tariff_plan.unit_measurement]


class ActivateOrExtend(BaseMain):
    def activate(self) -> None:
        if self.user.ws_status:
            return super().extend()
        else:
            return super().activate()


class VerificationOfFunds(ActivateOrExtend):
    def add_balance(self, count: float) -> None:
        if count < 0:
            raise COUNT_NOT_ZERO
        super().add_balance(count)

    def activate(self) -> None:
        if self.user.balance - self.user.tariff_plan.price < 0.:
            raise NOT_ENOUGH_FUNDS
        return super().activate()


class VerificationOfTariff(VerificationOfFunds):
    def activate(self) -> None:
        try:
            if self.user.tariff_plan is None or self.user.tariff_plan.archive:
                raise TARIFF_IS_NULL
            self.user.tariff_plan.archive = True
            super().activate()
            if self.user.is_new:
                self.user.is_new = False
        except:
            self.user.tariff_plan.archive = False
            raise


class Main(VerificationOfTariff):
    """
    using:
        User.balance
        User.tariff_plan
        User.tariff_plan.archive
        User.tariff_plan.price
        User.ws_status
        User.tariff_plan.unit_measurement
        User.balance
        User.start_datetime_pp
        User.end_datetime_pp
        User.start_datetime_pp
        User.is_new
        User.next_tariff_plan

        User, Tariff
    """
