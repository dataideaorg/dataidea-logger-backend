from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from .views import GoogleLoginAPI, GoogleCallbackAPI

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('user/', views.UserView.as_view(), name='user'),
    path('user/profile/', views.UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('google/login/', GoogleLoginAPI.as_view(), name='google_login'),
    path('google/callback/', GoogleCallbackAPI.as_view(), name='google_callback'),
]
