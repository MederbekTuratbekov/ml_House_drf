from rest_framework import status, generics, permissions, views
from .filters import PropertyFilter
from .models import UserProfile, Property, Review
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import CheckBuyerRoleReviews, CheckSellerRoleReviews
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (UserSerializer, LoginSerializer, UserProfileSerializer,
                          PropertySerializer, ReviewSerializer, CreatePropertySerializer,
                          CreateReviewSerializer, HousePredictSerializer)
import os
import joblib
from django.conf import settings


model_path = os.path.join(settings.BASE_DIR, 'lin_model.pkl')
model = joblib.load(model_path)

scaler_path = os.path.join(settings.BASE_DIR, 'scaler.pkl')
scaler = joblib.load(scaler_path)


class RegisterView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomLoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"detail": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)

        user = serializer.validated_data
        return Response(serializer.data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserProfileAPIView(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserProfile.objects.filter(id=self.request.user.id)


class PropertyAPIView(generics.ListAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = PropertyFilter
    ordering_fields = ['price', 'created_at', 'area']
    ordering = ['price']
    search_fields = ['title']

    def get_queryset(self):
        return Property.objects.select_related('seller').all()


class CreatePropertyAPIView(generics.CreateAPIView):
    serializer_class = CreatePropertySerializer
    permission_classes = [permissions.IsAuthenticated, CheckSellerRoleReviews]


class UpdateDeletePropertyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CreatePropertySerializer
    permission_classes = [permissions.IsAuthenticated, CheckSellerRoleReviews]

    def get_queryset(self):
        return Property.objects.filter(seller=self.request.user)


class ReviewAPIView(generics.ListAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']
    search_fields = ['comment']

    def get_queryset(self):
        return Review.objects.select_related('buyer', 'seller').all()


class CreateReviewAPIView(generics.CreateAPIView):
    serializer_class = CreateReviewSerializer
    permission_classes = [permissions.IsAuthenticated, CheckBuyerRoleReviews]


class UpdateDeleteReviewAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CreateReviewSerializer
    permission_classes = [permissions.IsAuthenticated, CheckBuyerRoleReviews]

    def get_queryset(self):
        return Review.objects.filter(buyer=self.request.user)


Neighborhood = ['Blueste', 'BrDale', 'BrkSide', 'ClearCr', 'CollgCr', 'Crawfor',
                'Edwards', 'Gilbert', 'IDOTRR', 'MeadowV', 'Mitchel', 'NAmes',
                'NPkVill', 'NWAmes', 'NoRidge', 'NridgHt', 'OldTown', 'SWISU',
                'Sawyer', 'SawyerW', 'Somerst', 'StoneBr', 'Timber', 'Veenker']


class PredictPriceAPIView(views.APIView):
    def post(self, request):
        serializer = HousePredictSerializer(data=request.data)

        if serializer.is_valid():
            valid_data = serializer.validated_data
            neighborhood = valid_data.get('Neighborhood')
            data_binary = [1 if neighborhood == i else 0 for i in Neighborhood]

            features = [
                valid_data['GrLivArea'],
                valid_data['YearBuilt'],
                valid_data['GarageCars'],
                valid_data['TotalBsmtSF'],
                valid_data['FullBath'],
                valid_data['OverallQual'],
            ] + data_binary

            scaled_data = scaler.transform([features])
            prediction = model.predict(scaled_data)[0]

            house_data = serializer.save(predicted_price=round(prediction, 2))
            return Response({'Predict': HousePredictSerializer(house_data).data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)