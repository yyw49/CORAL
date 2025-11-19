from rest_framework import permissions


class IsScheduleAssistant(permissions.BasePermission):
    """
    Permission check: User must be a schedule assistant (admin)
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        try:
            return request.user.lab_assistant.is_schedule_assistant
        except:
            return False


class IsOwnerOrScheduleAssistant(permissions.BasePermission):
    """
    Permission check: User can only access their own data unless they're admin
    """

    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        try:
            if request.user.lab_assistant.is_schedule_assistant:
                return True
        except:
            pass

        # Check if this is the user's own data
        if hasattr(obj, 'lab_assistant'):
            return obj.lab_assistant.user == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user

        return False