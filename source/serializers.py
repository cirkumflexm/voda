
from transliterate import translit

from django.db.utils import IntegrityError

from rest_framework import serializers
from account.models import User

from .models import *

class UserSerializer(serializers.ModelSerializer):

    class Meta:
       model = User

       fields = [
           'id', 'first_name', 'last_name', 'username', 'address', 'apartment', 'fias',
           'balance', 'ws_status', 'tariff_plan', 'start_datetime_pp', 'end_datetime_pp'
       ]
       read_only_fields = ['username', 'balance', 'ws_status', 'start_datetime_pp', 'end_datetime_pp']

    def create(self, validated_data, __i=0) -> None:
        __validated_data = validated_data.copy()
        if not validated_data.get("username"):
            __username = "".join(filter(
                lambda i: i.isalnum() or i in "@/./+/-/_",
                validated_data["first_name"].title() + validated_data["last_name"].title()
            ))
            __username += f"-{validated_data["fias"]}-{__i}"
            if __username.isascii():
                validated_data["username"] = __username
            validated_data["username"] = translit(__username, reversed=True)
        try:
            __user = super().create(validated_data)
            __user.groups.add(3)
            return __user
        except IntegrityError:
            return self.create(__validated_data, __i+1)


class TariffPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = TariffPlan
        fields = ['id', 'name', 'price', 'archive', 'unit_measurement']
        allows = ["GET", "POST", "PUT"]

    def __init__(self, *args, **kw) -> None:
        super().__init__(*args, **kw)
        if kw.get("context"):
            __request = kw.get("context", {}).get('request')
            try:
                assert __request
                assert not __request.user.groups.filter(id=1).exists()
                assert kw.get("context", {}).get("request") and kw["context"]["request"].method == "PUT"
                self.Meta.read_only_fields = ['id', 'name', 'price', 'unit_measurement']
            except AssertionError:
                self.Meta.read_only_fields = []
        pass