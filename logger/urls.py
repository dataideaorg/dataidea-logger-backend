from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api-keys', views.ApiKeyViewSet, basename='api-key')
router.register(r'event-logs', views.EventLogMessageViewSet, basename='event-log')
router.register(r'llm-logs', views.LlmLogMessageViewSet, basename='llm-log')

urlpatterns = [
    path('', include(router.urls)),
    path('user/stats/', views.get_user_stats, name='user-stats'),
    path('event-log/', views.create_event_log, name='create_event_log'),
    path('llm-log/', views.create_llm_log, name='create_llm_log'),
] 