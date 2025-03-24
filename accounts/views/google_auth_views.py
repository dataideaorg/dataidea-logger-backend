import requests
import json
from django.conf import settings
from django.shortcuts import redirect
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import login, get_user_model
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


User = get_user_model()


class GoogleLoginAPI(APIView):
    """
    API view to initiate Google OAuth login
    """
    def get(self, request):
        # Construct the Google OAuth URL
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        client_id = settings.GOOGLE_CLIENT_ID
        
        # Google OAuth URL parameters
        auth_url = f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=email%20profile&access_type=offline"
        
        # Return the auth URL to the frontend
        return Response({"auth_url": auth_url})
    

class GoogleCallbackAPI(APIView):
    """
    API view to handle Google OAuth callback and validate the auth code
    """
    def post(self, request):
        code = request.data.get('code')
        print('Code:', code)
        
        if not code:
            return Response({"error": "Authorization code is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Exchange the auth code for tokens
            token_url = "https://oauth2.googleapis.com/token"
            payload = {
                'code': code,
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                'grant_type': 'authorization_code'
            }
            
            # Make the request to Google
            response = requests.post(token_url, data=payload)
            token_data = response.json()
            
            # If there's an error, return it
            if 'error' in token_data:
                return Response({"error": token_data['error']}, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify the ID token
            id_info = id_token.verify_oauth2_token(
                token_data['id_token'], 
                google_requests.Request(), 
                settings.GOOGLE_CLIENT_ID
            )
            
            # Authenticate or create a user based on the email
            email = id_info.get('email')
            if not email:
                return Response({"error": "Email not provided by Google"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if email is verified
            if not id_info.get('email_verified', False):
                return Response({"error": "Email not verified with Google"}, status=status.HTTP_400_BAD_REQUEST)
            
            print('Creating user')
            # Get or create user
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],  
                }
            )

            print('User created')
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # Login the user
            print(user)
            
            return Response({
                "access_token": access_token,
                "refresh_token": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                },
                "created": created
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
