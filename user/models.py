from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from .utils import password_hasher

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


