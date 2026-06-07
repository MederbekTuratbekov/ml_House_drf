from rest_framework import serializers
from .models import UserProfile, Property, Review, HousePredict
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import os
import joblib
from django.conf import settings


model_path = os.path.join(settings.BASE_DIR, 'model_nb.pkl')
model = joblib.load(model_path)

vector_path = os.path.join(settings.BASE_DIR, 'vector.pkl')
vector = joblib.load(vector_path)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('username', 'email', 'password', 'first_name', 'last_name',
                  'phone_number', 'role', 'created_at')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = UserProfile.objects.create_user(**validated_data)
        return user

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'user': {
                'username': instance.username,
                'email': instance.email,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Неверные учетные данные")

    def to_representation(self, instance):
        refresh = RefreshToken.for_user(instance)
        return {
            'user': {
                'username': instance.username,
                'email': instance.email,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    created_at = serializers.DateField(format='%d-%m-%Y')
    class Meta:
        model = UserProfile
        fields = ('username', 'email', 'password', 'avatar', 'first_name',
                  'last_name', 'phone_number', 'role', 'created_at')
        extra_kwargs = {'password': {'write_only': True}}


class UserPublicInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('role', 'first_name', 'last_name', 'phone_number')


class PropertySerializer(serializers.ModelSerializer):
    created_at = serializers.DateField(format='%d-%m-%Y')
    seller = UserPublicInfoSerializer(read_only=True)
    class Meta:
        model = Property
        fields = ('title', 'description', 'property_type', 'region', 'city',
                  'district', 'address', 'area', 'price', 'rooms', 'floor',
                  'total_floors', 'condition', 'images', 'documents', 'seller', 'created_at')


class CreatePropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = ('title', 'description', 'property_type', 'region', 'city',
                  'district', 'address', 'area', 'price', 'rooms', 'floor',
                  'total_floors', 'condition', 'images', 'documents', 'seller')


class ReviewSerializer(serializers.ModelSerializer):
    created_at = serializers.DateField(format='%d-%m-%Y')
    buyer = UserPublicInfoSerializer(read_only=True)
    seller = UserPublicInfoSerializer(read_only=True)
    check_comments = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ('buyer', 'seller', 'rating', 'comment', 'created_at', 'check_comments')

    def get_check_comments(self, obj):
        return model.predict(vector.transform([obj.comment]))


class CreateReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ('seller', 'rating', 'comment', 'buyer')


class HousePredictSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousePredict
        fields = '__all__'