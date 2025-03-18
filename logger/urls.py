from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'api-keys', views.ApiKeyViewSet, basename='api-key')
router.register(r'event-logs', views.EventLogMessageViewSet, basename='event-log')
router.register(r'llm-logs', views.LlmLogMessageViewSet, basename='llm-log')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('user/', views.UserView.as_view(), name='user'),
    path('user/profile/', views.UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('user/stats/', views.get_user_stats, name='user-stats'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('event-log/', views.create_event_log, name='create_event_log'),
    path('llm-log/', views.create_llm_log, name='create_llm_log'),
] 