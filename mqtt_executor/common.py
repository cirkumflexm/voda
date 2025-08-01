
import paho.mqtt.client as mqtt

from account.models import User


CLIENT = mqtt.Client()


def set_ws_status_on(user: User) -> None:
    CLIENT.publish(f"MX210/{user.encoarded.device.name}/SET/"
                    f"DI{user.encoarded.number}/1")