from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import LabAssistant
from accounts.serializers import RegisterSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    POST /api/register/
    
    Register a new user with USC email validation
    
    Request body:
    {
        "email": "student@usc.edu",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe"
    }
    """
    serializer = RegisterSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Get lab assistant info
        lab_assistant = user.labassistant
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Registration successful',
            'user': {
                'id': str(user.id),
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'role': lab_assistant.role,
                'avatar': '',
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    POST /api/login/
    
    Login with email and password, returns JWT tokens
    
    Request body:
    {
        "email": "student@usc.edu",
        "password": "password123"
    }
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {"detail": "Email and password required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get user by email
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Authenticate (checks password hash)
    user = authenticate(username=user.username, password=password)
    if user is None:
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get role from LabAssistant
    try:
        lab_assistant = user.labassistant
        role = lab_assistant.role
    except LabAssistant.DoesNotExist:
        role = 'ra'  # Default role if LabAssistant doesn't exist

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    # Return user data + tokens
    return Response({
        "user": {
            "id": str(user.id),
            "name": user.get_full_name() or user.username,
            "email": user.email,
            "role": role,
            "avatar": "",
        },
        "tokens": {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    POST /api/logout/
    
    Blacklist the refresh token to invalidate it
    
    Request body:
    {
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response(
            {"detail": "Logged out successfully"}, 
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    GET /api/me/
    
    Get current logged-in user's information
    Requires: Authorization: Bearer <access_token>
    """
    try:
        lab_assistant = request.user.labassistant
        
        return Response({
            'id': str(request.user.id),
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
            'role': lab_assistant.role,
            'avatar': '',
        })
    except LabAssistant.DoesNotExist:
        return Response(
            {'detail': 'Lab assistant profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )