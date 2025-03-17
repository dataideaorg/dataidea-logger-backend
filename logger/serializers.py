from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ApiKey, LogMessage

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        read_only_fields = ['id']

class UserProfileSerializer(serializers.ModelSerializer):
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'current_password', 'new_password']
        
    def validate(self, data):
        # If changing password, current_password is required
        if 'new_password' in data and not data.get('current_password'):
            raise serializers.ValidationError({"current_password": "Current password is required to set a new password"})
            
        # Verify current password if provided
        if 'current_password' in data:
            user = self.instance
            if not user.check_password(data['current_password']):
                raise serializers.ValidationError({"current_password": "Current password is incorrect"})
                
        return data
        
    def update(self, instance, validated_data):
        # Handle password update
        if 'new_password' in validated_data:
            instance.set_password(validated_data['new_password'])
            validated_data.pop('new_password')
        
        # Remove current_password from data to update
        if 'current_password' in validated_data:
            validated_data.pop('current_password')
            
        # Update other fields
        return super().update(instance, validated_data)

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user

class ApiKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApiKey
        fields = ['id', 'key', 'name', 'created_at', 'is_active']
        read_only_fields = ['id', 'key', 'created_at']

class LogMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogMessage
        fields = ['id', 'user_id', 'query', 'response', 'level', 'timestamp', 'metadata']
        read_only_fields = ['id', 'timestamp']

class LogMessageCreateSerializer(serializers.ModelSerializer):
    api_key = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = LogMessage
        fields = ['api_key', 'user_id', 'query', 'response', 'level', 'metadata']
    
    def validate_api_key(self, value):
        try:
            api_key = ApiKey.objects.get(key=value, is_active=True)
            return api_key
        except ApiKey.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive API key")
    
    def create(self, validated_data):
        api_key = validated_data.pop('api_key')
        log_message = LogMessage.objects.create(api_key=api_key, **validated_data)
        return log_message 