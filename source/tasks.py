
import logging

from django.utils import timezone

from .src.tools import pay_service, CustomException, service_deactivation
from .models import *


logger = logging.getLogger(__name__)


def renewal_condition_services() -> None:
    __users_iter = (
        QuerySet(User)
        .filter(
            ws_status=True,
            event_date__lt=timezone.now()
        )
    )

    for user in __users_iter:
        try:
            pay_service(user)
        except CustomException:
            service_deactivation(user)
        except Exception as ex:
            logger.critical(ex)

    QuerySet(User).bulk_update(__users_iter, ("balance", "ws_status", "start_datetime_pp", "end_datetime_pp"))


