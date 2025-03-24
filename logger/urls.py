from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api-keys', views.ApiKeyViewSet, basename='api-key')
router.register(r'event-logs', views.EventLogMessageViewSet, basename='event-log')
router.register(r'llm-logs', views.LlmLogMessageViewSet, basename='llm-log')
router.register(r'projects', views.ProjectViewSet, basename='project')

urlpatterns = [
    path('', include(router.urls)),
    path('user/stats/', views.get_user_stats, name='user-stats'),
    path('analytics/', views.get_analytics_data, name='analytics'),
    path('analytics/download/<str:data_type>/', views.download_analytics_csv, name='download_analytics'),
    path('event-log/', views.create_event_log, name='create_event_log'),
    path('llm-log/', views.create_llm_log, name='create_llm_log'),
    path('download/all-logs/', views.download_all_logs, name='download_all_logs'),
] 