from django.contrib.auth import authenticate, logout
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.models import User
from accounts.models import LabAssistant


@api_view(['POST'])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {"detail": "Email and password required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # assuming username == email, or you can look up by email first
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=user.username, password=password)
    if user is None:
        return Response(
            {"detail": "Invalid credentials"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # get role from LabAssistant
    try:
        lab_assistant = user.labassistant
        role = lab_assistant.role
    except LabAssistant.DoesNotExist:
        # if you have other types of users, decide what to do here
        role = 'ra'  # or raise error

    # this JSON shape matches your frontend's `User` type
    return Response({
        "id": str(user.id),
        "name": user.get_full_name() or user.username,
        "email": user.email,
        "role": role,
        "avatar": "",  # you can add a real avatar field later
    })

@api_view(['POST'])
def logout_view(request):
    # This clears the Django session
    logout(request)
    return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)