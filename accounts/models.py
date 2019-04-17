from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
import re


class CustomUserManager(BaseUserManager):

    def _create_user(
            self, phone_number,
            first_name, second_name,
            street, house, apartment='', password=None,
            email=None, date_of_birth=None, is_admin=False, is_guest=False
            ):

        if not phone_number:
            # TODO calling create_user allows to bypass all required fields,
            # if not checked this way
            raise ValueError('Users must have a phone number')

        if is_guest is False:
            """
            Phone number and email are unique for registered users.
            """
            registered_users = self.model.objects.filter(is_guest=False)
            if password is None:
                raise ValueError('Registering users must have a password')
            if (email is not None and
                    registered_users.filter(email=email).exists()):
                raise ValueError('This email is already registered')
            if registered_users.filter(phone_number=phone_number).exists():
                raise ValueError('This phone number is already registered')

        user = self.model(
            phone_number=re.sub('\D', '', phone_number),
            first_name=first_name,
            second_name=second_name,
            street=street,
            house=house,
            apartment=apartment,
            email=self.normalize_email(email),
            date_of_birth=date_of_birth,
            is_admin=is_admin,
            is_guest=is_guest
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

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

        return self._create_user(
            phone_number, first_name, second_name, street,
            house, apartment, password, email, date_of_birth
        )

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
        return self._create_user(
            phone_number, first_name, second_name, street,
            house, apartment, password, email, date_of_birth, True
        )

    def create_guest_user(
            self, phone_number,
            first_name, second_name,
            street, house, apartment='', email=None
            ):
        """
        Creates and saves a guest user with the given phone number, password,
        full address and optional email and date of birth.
        """
        return self._create_user(
            phone_number=phone_number,
            first_name=first_name,
            second_name=second_name,
            street=street,
            house=house,
            apartment=apartment,
            email=email,
            is_admin=False,
            is_guest=True
        )


class User(AbstractBaseUser):
    # TODO max length etc.
    phone_number = models.CharField(
        max_length=64,
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
        blank=True,
        null=True
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)
    is_guest = models.BooleanField(default=False)
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
