from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.fields import CharField
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(AbstractUser):
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = PhoneNumberField(blank=True, null=True, unique=True)
    email = models.EmailField(unique=True)
    ROLE_CHOICES = [
        ('admin', 'admin'),
        ('seller', 'seller'),
        ('buyer', 'buyer')
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.username} ({self.role})'


class Property(models.Model):
    title = models.CharField(max_length=500)
    description = models.TextField()

    PROPERTY_TYPE = (
        ('apartment', 'apartment'),
        ('house', 'house'),
        ('commercial_property', 'commercial_property'),
        ('room', 'room'),
        ('land_plot_or_lot', 'land_plot_or_lot'),
        ('summer_house_or_country_house', 'summer_house_or_country_house'),
        ('parking_space_or_garage', 'parking_space_or_garage')
    )
    property_type = models.CharField(choices=PROPERTY_TYPE, max_length=50)  # Исправлено

    CHOICE_REGION = (
        ('Chui', 'Chui'), ('Talas', 'Talas'), ('Jal_Abad', 'Jalal_Abad'),
        ('Osh', 'Osh'), ('Batken', 'Batken'), ('Ysyk_Kol', 'Ysyk_Kol'), ('Naryn', 'Naryn')
    )
    region = models.CharField(choices=CHOICE_REGION, max_length=20)

    CHOICE_CITY = (
        ('Bishkek', 'Bishkek'), ('Talas', 'Talas'), ('Jal_Abad', 'Jalal_Abad'),
        ('Osh', 'Osh'), ('Batken', 'Batken'), ('Kara_Kol', 'Kara_Kol'), ('Naryn', 'Naryn')
    )
    city = models.CharField(choices=CHOICE_CITY, max_length=20)

    district = models.CharField(max_length=100)
    address = models.CharField(max_length=100)

    area = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(1000)], blank=True,
                                       null=True)
    price = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(9999999999)], default=1)
    rooms = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(20)], blank=True, null=True)
    floor = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], blank=True,
                                        null=True)
    total_floors = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)], blank=True,
                                               null=True)

    CHOICE_CONDITION = (
        ('excellent', 'excellent'),
        ('normal', 'normal'),
        ('needs_repair', 'needs_repair')
    )
    condition = models.CharField(choices=CHOICE_CONDITION, default='excellent', max_length=20, null=True, blank=True)
    images = models.ImageField(upload_to='property_images/')
    documents = models.BooleanField(default=True)
    seller = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.seller.username} | {self.title[:30]}'

class Review(models.Model):
    buyer = models.ForeignKey(UserProfile,on_delete=models.CASCADE, related_name='buyer')
    seller = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='seller')
    rating = models.PositiveIntegerField(choices=[(i, str(i))for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.buyer} {self.rating} {self.comment}'

class HousePredict(models.Model):
    GrLivArea = models.IntegerField()
    YearBuilt = models.IntegerField()
    GarageCars = models.IntegerField()
    TotalBsmtSF = models.IntegerField()
    FullBath = models.IntegerField()
    OverallQual = models.IntegerField()
    Neighborhood = models.CharField(max_length=50)
    predicted_price = models.FloatField(null=True, blank=True)
