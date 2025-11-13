from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from accounts.models import LabAssistant
from accounts.service import AvailabilityService, ScheduleService, StudyService

@api_view(['GET'])
def labassistant_availability(request):
    """
    GET endpoint to return a LabAssistant's availability JSON.
    Only includes slots where the assistant is available.

    Query params:
        user_id: int

    Response format:
    {
        "lab_assistant_id": 3,
        "user_id": 7,
        "availability": {
            "monday": [0, 2, 3, ...],
            "tuesday": [1, 5, 6, ...],
            "wednesday": [...],
            "thursday": [...],
            "friday": [...]
        }
    }
    """
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response({"error": "Missing user_id parameter"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        assistant = user.lab_assistant
    except LabAssistant.DoesNotExist:
        return Response({"error": "LabAssistant not found for this user"}, status=status.HTTP_404_NOT_FOUND)

    # Get or create availability
    availability = getattr(assistant, 'availability', None)
    if not availability:
        availability = AvailabilityService.create_availability(assistant)

    # Serialize compact availability as JSON
    availability_json = {}
    for day_index, day_name in enumerate(availability.DAYS):
        day_obj = getattr(availability, day_name)
        # only include slots that are available
        available_slots = [int(slot) for slot, val in day_obj.slots.items() if val == 1]
        availability_json[day_name] = available_slots

    return Response({
        "lab_assistant_id": assistant.id,
        "user_id": user.id,
        "availability": availability_json
    })


@api_view(['POST'])
def update_labassistant_availability(request):
    """
    POST endpoint to update a LabAssistant's availability.
    Expects:
        user_id: int (query param)
        availability: dict in request.data
            Each day contains a list of available slot indices.
            Example:
            {
                "monday": [0, 2, 3],
                "tuesday": [1, 4, 5],
                "wednesday": [],
                "thursday": [0, 1, 2],
                "friday": [5, 6, 7]
            }
    """
    user_id = request.query_params.get('user_id')
    if not user_id:
        return Response({"error": "Missing user_id parameter"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        assistant = user.lab_assistant
    except LabAssistant.DoesNotExist:
        return Response({"error": "LabAssistant not found for this user"}, status=status.HTTP_404_NOT_FOUND)

    availability_data = request.data.get("availability")
    if availability_data is None:
        return Response({"error": "Missing availability data"}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure assistant has an Availability object
    availability = getattr(assistant, 'availability', None)
    if not availability:
        availability = AvailabilityService.create_availability(assistant)

    # Update each day
    for day_index, day_name in enumerate(availability.DAYS):
        slots_list = availability_data.get(day_name)
        if slots_list is None:
            continue  # skip missing day

        day_obj = getattr(availability, day_name)
        # Reset all slots to unavailable
        day_obj.slots = {str(i): 0 for i in range(AvailabilityService.SLOTS_PER_DAY)}
        # Set provided slots to available
        for slot_index in slots_list:
            AvailabilityService.set_slot(assistant, day_index, slot_index, True)

    return Response({"message": "Availability updated successfully"})