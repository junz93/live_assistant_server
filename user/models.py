from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, username, mobile_phone, password, **extra_fields):
        if not username or not mobile_phone or not password:
            raise ValueError('Users must have username, mobile phone, and password')
        
        user = self.model(username=username, mobile_phone=mobile_phone)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, mobile_phone, password, **extra_fields):
        return self.create_user(username, mobile_phone, password, extra_fields)

class User(AbstractBaseUser):
    username = models.CharField(max_length=150, unique=True)
    mobile_phone = models.CharField(max_length=11, unique=True)
    created_datetime = models.DateTimeField(auto_now_add=True, editable=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['mobile_phone']

    # @classmethod
    # def from_dict(cls, data: dict):
    #     user = cls()
    #     user.copy_from_dict(data)
    #     return user

    # def copy_from_dict(self, data: dict):
    #     self.mobile_phone = data.get('mobile_phone')
    #     self.username = self.mobile_phone
    #     if 'password' in data:
    #         self.password_hash = password_hasher.hash(data['password'])

class Subscription(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    expiry_datetime = models.DateTimeField()
    created_datetime = models.DateTimeField(auto_now_add=True, editable=False)
    updated_datetime = models.DateTimeField(auto_now=True, editable=False)

class SubscriptionProductId:
    SP1 = 'SP1'
    SP2 = 'SP2'
    SP3 = 'SP3'

SUBSCRIPTION_PRODUCTS = {
    SubscriptionProductId.SP1: {
        'id': SubscriptionProductId.SP1,
        # 'price': '540.00',
        'price': '3.00',
        'time_months': 12,
        'order_product_name': '主播AI助手 一年会员',
    },
    SubscriptionProductId.SP2: {
        'id': SubscriptionProductId.SP2,
        # 'price': '180.00',
        'price': '2.00',
        'time_months': 3,
        'order_product_name': '主播AI助手 三个月会员',
    },
    SubscriptionProductId.SP3: {
        'id': SubscriptionProductId.SP3,
        # 'price': '90.00',
        'price': '1.00',
        'time_months': 1,
        'order_product_name': '主播AI助手 一个月会员',
    },
}

class SubscriptionOrder(models.Model):
    PRODUCT_ID_CHOICES = [
        (SubscriptionProductId.SP1, '包年'),
        (SubscriptionProductId.SP2, '包季'),
        (SubscriptionProductId.SP3, '包月'),
    ]

    ORDER_ID_PREFIX = 'SUBS'

    order_id = models.CharField(max_length=64, primary_key=True)
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    product_id = models.CharField(max_length=8, choices=PRODUCT_ID_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    amount_str = models.CharField(max_length=15)
    created_datetime = models.DateTimeField(auto_now_add=True, editable=False)
    paid_datetime = models.DateTimeField(null=True, blank=True)
