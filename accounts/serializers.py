from rest_framework import serializers
from django.contrib.auth.models import User

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

    def validate_email(self, value):
        # Check if email is already in use by another user
        user = self.instance
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email is already in use by another account.")
        return value

    def validate_username(self, value):
        # Check if username is already in use by another user
        user = self.instance
        if User.objects.filter(username=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

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

        # Update username and email
        if 'username' in validated_data:
            instance.username = validated_data['username']
        if 'email' in validated_data:
            instance.email = validated_data['email']

        instance.save()
        return instance
    

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
    