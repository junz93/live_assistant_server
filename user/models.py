from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone

import datetime


class UserManager(BaseUserManager):
    def create_user(self, username, mobile_phone, password, **extra_fields):
        if not username or not mobile_phone or not password:
            raise ValueError('Users must have username, mobile phone, and password')
        
        user = self.model(username=username, mobile_phone=mobile_phone)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, username, mobile_phone, password, **extra_fields):
        return self.create_user(username, mobile_phone, password, **extra_fields)


class User(AbstractBaseUser):
    username = models.CharField(max_length=150, unique=True)
    mobile_phone = models.CharField(max_length=11, unique=True)
    created_datetime = models.DateTimeField(auto_now_add=True, editable=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['mobile_phone']


class SubscriptionStatus:
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'


class Subscription(models.Model):
    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    expiry_datetime = models.DateTimeField()
    created_datetime = models.DateTimeField(auto_now_add=True, editable=False)
    updated_datetime = models.DateTimeField(auto_now=True, editable=False)

    # def get_status(self):
    #     return SubscriptionStatus.ACTIVE if self.expiry_datetime > timezone.now() else SubscriptionStatus.INACTIVE
    
    # def get_expiry_timestamp(self):
    #     return int(self.expiry_datetime.timestamp())
    
    @classmethod
    def get_unique(cls, user: User):
        try:
            return cls.objects.get(user_id=user.id)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_status(cls, subscription):
        if not subscription:
            return SubscriptionStatus.INACTIVE
        # return subscription.get_status()
        return SubscriptionStatus.ACTIVE if subscription.expiry_datetime > timezone.now() else SubscriptionStatus.INACTIVE
    
    @classmethod
    def get_expiry_timestamp(cls, subscription):
        if not subscription:
            return None
        return int(subscription.expiry_datetime.timestamp())


class SubscriptionProductId:
    SP1 = 'SP1'
    SP2 = 'SP2'
    SP3 = 'SP3'


SUBSCRIPTION_PRODUCTS = {
    SubscriptionProductId.SP1: {
        'id': SubscriptionProductId.SP1,
        # 'price': '540.00',
        'price': '1.50',
        'time_months': 12,
        'order_product_name': '主播AI助手 一年会员',
    },
    SubscriptionProductId.SP2: {
        'id': SubscriptionProductId.SP2,
        # 'price': '180.00',
        'price': '1.00',
        'time_months': 3,
        'order_product_name': '主播AI助手 三个月会员',
    },
    SubscriptionProductId.SP3: {
        'id': SubscriptionProductId.SP3,
        # 'price': '90.00',
        'price': '0.50',
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


# TODO: add unique index for (user, date)
class Usage(models.Model):
    MAX_TIME_SECONDS = {
        SubscriptionStatus.ACTIVE: 18000,   # 5 hours
        SubscriptionStatus.INACTIVE: 3600,  # 1 hours
    }

    user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    date = models.DateField()
    time_seconds = models.IntegerField(default=0)
    # updated_datetime = models.DateTimeField(auto_now=True)
    updated_datetime = models.DateTimeField(default=timezone.now)

    @classmethod
    def get_unique(cls, user: User, today: datetime.date, create: bool = False):
        try:
            return cls.objects.get(user_id=user.id, date=today)
        except cls.DoesNotExist:
            return cls(user=user, date=today) if create else None
        
    @classmethod
    def get_time_seconds(cls, usage):
        return usage.time_seconds if usage else 0
    
    @classmethod
    def get_remaining_time_seconds(cls, usage, subscription):
        max_time_seconds = cls.MAX_TIME_SECONDS[Subscription.get_status(subscription)]
        time_seconds = cls.get_time_seconds(usage)
        return max(max_time_seconds - time_seconds, 0)
