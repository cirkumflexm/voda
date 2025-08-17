from decimal import Decimal
from typing import TypeVar, Callable
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import QuerySet

from account.models import User
from device.common import set_ws_status_on
from payment.models import Payment
from tariff.models import TariffPlan, ServiceArchive


UserId = TypeVar("UserId", bound=int)


class CustomException(Exception):
    pass


NOT_ENOUGH_FUNDS = CustomException("NotEnoughFunds", "Недостаточно средств")
COUNT_NOT_ZERO = CustomException("COUNT_NOT_ZERO", "Пополняемое средство не может быть нулем")
TARIFF_IS_NULL = CustomException("TARIFF_IS_NULL", "Тариф не определен")


class BaseMain:
    def __init__(self, user: User, payment_id: str = None) -> None:
        self.user = user
        self.now_datetime = timezone.now()
        self.payment_id = payment_id

    def add_balance(self, count: float) -> None:
        self.user.balance += Decimal(count)
        QuerySet(Payment).create(
            user=self.user,
            quantity=Decimal(count),
            payment=self.payment_id
        )

    def activate(self) -> None:
        if self.user.tariff_plan.is_test:
            self.user.is_new = False
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
        # set_ws_status_on(self.user)
        self.user.ws_status = True

    def extend(self) -> None:
        self.user.balance -= self.user.tariff_plan.price
        self.user.end_datetime_pp += {
            "day": relativedelta(days=1),
            "month": relativedelta(months=1),
            "quarter": relativedelta(months=3),
            "halfyear": relativedelta(months=6),
            "year": relativedelta(years=1),
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
        if self.user.tariff_plan is None or self.user.tariff_plan.archive:
            raise TARIFF_IS_NULL
        return super().activate()


class Main(VerificationOfTariff):
    pass
