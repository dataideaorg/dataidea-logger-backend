from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User
from .models import ApiKey, LogMessage
from .serializers import (
    UserSerializer, UserRegistrationSerializer, ApiKeySerializer, 
    LogMessageSerializer, LogMessageCreateSerializer, UserProfileSerializer
)

# Create your views here.

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class UserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class UserProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return updated user data
        return Response(UserSerializer(instance).data)

class ApiKeyViewSet(viewsets.ModelViewSet):
    serializer_class = ApiKeySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ApiKey.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LogMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LogMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return LogMessage.objects.filter(api_key__user=user)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_log_message(request):
    serializer = LogMessageCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
