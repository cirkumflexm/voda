import logging

from yookassa import Configuration, Payment
from yookassa.domain.exceptions import ApiError
from yookassa.domain.common.user_agent import Version
from yookassa.domain.response import PaymentResponse
from dotenv import load_dotenv
from os import getenv

load_dotenv()


__all__ = [
    "ApiError", "create_payment", "find_payment", "capture_payment", "Payment"
]


Configuration.account_id = getenv("SHOP_ID")
Configuration.secret_key = getenv("SECRET_KEY")
Configuration.configure_user_agent(framework=Version('Django', '5.2.0'))


def create_payment(
        *, num: int, price: float, currency: str,
        tariff_name: str, full_name: str,
        user_phone: str, user_email: str,
        user_id: int, tariff_id: int
) -> dict:
    payment = Payment.create(
        {
            "amount": {
                "value": price,
                "currency": currency
            },
            "save_payment_method": True,
            "receipt": {
                "customer": {
                    "full_name": full_name,
                    "phone": user_phone,
                    **({"email": user_email} if user_email else {})
                },
                "items": [
                    {
                        "description": tariff_name,
                        "amount": {
                            "value": price,
                            "currency": currency
                        },
                        "vat_code": 2,   # НДС по ставке 0%
                        "quantity": 1,
                        "measure": "piece"
                    }
                ]
            },
            "confirmation": {
                "type": "embedded"
            },
            "capture": True,
            "description": f"Заказ №{num}",
            "metadata": {
                "user_id": user_id,
                "tariff_id": tariff_id
            }
        }
    )
    return {
        "user_id": user_id,
        "tariff_id": tariff_id,
        "response_data": {
            "id": payment.id,
            "description": payment.description,
            "created_at": payment.created_at,
            "amount": {
                "currency": payment.amount.currency,
                "confirmation_url": payment.amount.value,
            },
            "confirmation": {
                "type": payment.confirmation["type"],
                "confirmation_token": payment.confirmation["confirmation_token"]
            }
        }
    }


def create_auto_payment(
        *, num: int, price: float, currency: str,
        payment_method_id: str
) -> str:
    payment = Payment.create({
        "amount": {
            "value": price,
            "currency": currency
        },
        "capture": True,
        "payment_method_id": payment_method_id,
        "description": f"Заказ №{num}"
    })
    return payment.id


def find_payment(*, payment_id: str) -> PaymentResponse:
    return Payment.find_one(payment_id)


def capture_payment(*, payment_id: str) -> PaymentResponse:
    return Payment.capture(payment_id=payment_id)
