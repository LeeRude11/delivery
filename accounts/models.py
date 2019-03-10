from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
import re


class CustomUserManager(BaseUserManager):
    def create_user(
            self, phone_number, password,
            first_name, second_name,
            street, house, apartment='',
            email=None, date_of_birth=None
            ):
        """
        Creates and saves a User with the given phone number, password,
        full address and optional email and date of birth.
        """
        if not phone_number:
            # TODO calling create_user allows to bypass all required fields,
            # if not checked this way
            raise ValueError('Users must have a phone number')

        user = self.model(
            phone_number=re.sub('\D', '', phone_number),
            first_name=first_name,
            second_name=second_name,
            email=self.normalize_email(email),
            date_of_birth=date_of_birth,
            street=street,
            house=house,
            apartment=apartment
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
            self, phone_number, password,
            first_name, second_name,
            street, house, apartment='',
            email=None, date_of_birth=None
            ):
        """
        Creates and saves a superuser with the given phone number, password,
        full address and optional email and date of birth.
        """
        # TODO superuser-s might need an email
        # TODO create a superuser without create_user fields(address)?
        user = self.create_user(
            phone_number=phone_number,
            password=password,
            first_name=first_name,
            second_name=second_name,
            email=email,
            date_of_birth=date_of_birth,
            street=street,
            house=house,
            apartment=apartment
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    # TODO max length etc.
    phone_number = models.CharField(
        max_length=64,
        unique=True
    )
    first_name = models.CharField(max_length=64)
    second_name = models.CharField(max_length=64)
    street = models.CharField(
        max_length=64,
        verbose_name='street name'
    )
    house = models.CharField(
        max_length=64,
        verbose_name='house number'
    )
    apartment = models.CharField(
        max_length=64,
        verbose_name='apartment, suite or room number',
        blank=True
    )
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = [
        'first_name',
        'second_name',
        'street',
        'house',
    ]

    def __str__(self):
        return self.phone_number

    def get_full_name(self):
        return f'{self.first_name} {self.second_name}'

    def get_short_name(self):
        return f'{self.first_name} {self.second_name[0]}.'

    # TODO permissions
    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin
