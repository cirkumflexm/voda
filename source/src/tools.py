from decimal import Decimal
from typing import TypeVar, Callable
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.db.models import QuerySet

from account.models import User
from mqtt_executor.common import set_ws_status_on
from payment.models import Payment
from source.models import TariffPlan, ServiceArchive


UserId = TypeVar("UserId", bound=int)


class CustomException(Exception):
    pass


NOT_ENOUGH_FUNDS = CustomException("NotEnoughFunds", "Недостаточно средств")
COUNT_NOT_ZERO = CustomException("COUNT_NOT_ZERO", "Пополняемое средство не может быть нулем")
TARIFF_IS_NULL = CustomException("TARIFF_IS_NULL", "Тариф не определен")


class MainAbs:
    def __init__(self, user: User, payment_id: str) -> None:
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
        set_ws_status_on(self.user)

    def extend(self) -> None:
        self.user.balance -= self.user.tariff_plan.price
        self.user.end_datetime_pp = self.user.end_datetime_pp + {
            "day": relativedelta(days=1),
            "month": relativedelta(months=1),
            "quarter": relativedelta(months=3),
            "halfyear": relativedelta(months=6),
            "year": relativedelta(years=1),
        }[self.user.tariff_plan.unit_measurement]


class ActivateOrExtend(MainAbs):
    def activate(self) -> None:
        if self.user.ws_status is True:
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


# class __Exc(CustomException):
#     def __new__(cls, name: str, msg: str) -> Exception:
#         cls.__qualname__ = name
#         cls.__str__ = lambda _: msg
#         return super().__new__(cls)
#
# NOT_ENOUGH_FUNDS = __Exc("NotEnoughFunds", "Недостаточно средств")
#
#
# def _writing_off_money(user: User) -> None:
#     __tariff_plan = user.tariff_plan
#     if user.balance < __tariff_plan.price:
#         raise NOT_ENOUGH_FUNDS
#     user.balance -= __tariff_plan.price
#
#
# def _tariff_period(user: User, now_datetime: timezone) -> None:
#     user.start_datetime_pp = now_datetime
#     user.end_datetime_pp = now_datetime + {
#         "day": relativedelta(days=1),
#         "month": relativedelta(months=1),
#         "quarter": relativedelta(months=3),
#         "halfyear": relativedelta(months=6),
#         "year": relativedelta(years=1),
#     }[user.tariff_plan.unit_measurement]
#
#
# def _service_activation(user: User) -> None:
#     __now_datetime = timezone.now()
#
#     _tariff_period(user, __now_datetime)
#
#     QuerySet(ServiceArchive).create(
#         user=user,
#         start_datetime_pp=user.start_datetime_pp,
#         end_datetime_pp=user.end_datetime_pp,
#         tariff_plan=user.tariff_plan
#     )
#
#     user.ws_status = True
#
#
# def _service_deactivation(user: User) -> None:
#     user.ws_status = False
#
#
# def _pay_service(user: User) -> None:
#     _writing_off_money(user)
#     _service_activation(user)
#
#
# def _crediting_funds(user: User, quantity: float) -> None:
#     user.balance += Decimal(quantity)
#
#     _pay_service(user)
#
#     QuerySet(Payment).create(
#         user=user,
#         quantity=quantity,
#         datetime=timezone.now()
#     )
#
#     user.save(force_update=('balance', 'start_datetime_pp', 'end_datetime_pp', 'ws_status'))
#
#
# class Action:
#     def __init__(self, func: Callable, **kw) -> None:
#         self.func = func
#         self.kw = kw
#
#     def __call__(self, user: User | UserId, *args, **kw) -> User:
#         if not isinstance(user, User):
#             user = (
#                 QuerySet(User)
#                 .select_related("tariff_plan")
#                 .get(id=user)
#             )
#         else:
#             if "tariff_plan" not in user.__dir__():
#                 user.tariff_plan = QuerySet(TariffPlan).get(id=getattr(user, "tariff_plan_id"))
#
#         self.func(user, *args, **kw)
#
#         return user
#
#
# service_activation = Action(_service_activation)
# service_deactivation = Action(_service_deactivation)
# pay_service = Action(_pay_service)
# crediting_funds = Action(_crediting_funds)
