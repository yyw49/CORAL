from accounts.models import Availability, LabAssistant, Day, Schedule, Study
from datetime import time

class AvailabilityService:
    SLOTS_PER_DAY = Day.SLOTS_PER_DAY

    # Validations
    @staticmethod
    def validate_slot_index(slot_index: int):
        if slot_index < 0 or slot_index >= AvailabilityService.SLOTS_PER_DAY:
            raise ValueError(f"slot_index must be in range [0, {AvailabilityService.SLOTS_PER_DAY-1}]")

    @staticmethod
    def validate_day_index(day_index: int):
        if day_index < 0 or day_index >= 5:
            raise ValueError("day_index must be 0 (Monday) to 4 (Friday)")

    @staticmethod
    def get_day_slots(avail: Availability, day_index: int):
        AvailabilityService.validate_day_index(day_index)
        day_name = Availability.DAYS[day_index]
        return getattr(avail, day_name)

    # Availability methods
    @staticmethod
    def set_slot_for_assistant(availability: Availability, day_index: int, slot_index: int, assistant: LabAssistant, available: bool):
        AvailabilityService.validate_slot_index(slot_index)
        slots = AvailabilityService.get_day_slots(availability, day_index)
        slot = slots[slot_index]['assistants']
        aid = int(assistant.id)
        if available and aid not in slot:
            slot.append(aid)
        elif not available and aid in slot:
            slot.remove(aid)
            # clear any scheduled study for this assistant in this slot if it exists + making unavailable
            if 'scheduled_studies' in slots[slot_index]:
                slots[slot_index]['scheduled_studies'].pop(str(aid), None)
        # save 
        setattr(availability, Availability.DAYS[day_index], slots)
        availability.save(update_fields=[Availability.DAYS[day_index]])

    @staticmethod
    def set_interval_for_assistant(availability: Availability, day_index: int, start: int, end: int, assistant: LabAssistant, available: bool = True):
        for i in range(start, end):
            AvailabilityService.set_slot_for_assistant(availability, day_index, i, assistant, available)

    @staticmethod
    def slot_has_assistant(availability: Availability, day_index: int, slot_index: int, assistant: LabAssistant) -> bool:
        AvailabilityService.validate_slot_index(slot_index)
        slots = AvailabilityService.get_day_slots(availability, day_index)
        return int(assistant.id) in slots[slot_index]['assistants']

    @staticmethod
    def is_available_for_interval(availability: Availability, day_index: int, start: int, end: int, assistant: LabAssistant) -> bool:
        return all(AvailabilityService.slot_has_assistant(availability, day_index, i, assistant) for i in range(start, end))


class ScheduleService:

    @staticmethod
    def get_day(schedule: Schedule, day_index: int) -> Day:
        if day_index < 0 or day_index >= 5:
            raise ValueError("day_index must be 0 (Monday) to 4 (Friday)")
        day_name = Schedule.DAYS[day_index]
        return getattr(schedule, day_name)

    @staticmethod
    def study_is_scheduled(schedule: Schedule, day_index: int, start: int, end: int, recipient: LabAssistant) -> bool:
        day = ScheduleService.get_day(schedule, day_index)
        for i in range(start, end):
            if str(recipient.id) in day.slots[i].get('scheduled_studies', {}):
                return True
        return False

    @staticmethod
    def set_study_for_slot(schedule: Schedule, day_index: int, start: int, end: int, recipient: LabAssistant, study: Study):
        day = ScheduleService.get_day(schedule, day_index)
        for i in range(start, end):
            if 'scheduled_studies' not in day.slots[i]:
                day.slots[i]['scheduled_studies'] = {}
            day.slots[i]['scheduled_studies'][str(recipient.id)] = study.id
        day.save(update_fields=['slots'])

    @staticmethod
    def schedule_study(scheduler: LabAssistant, recipient: LabAssistant, day_index: int, start: int, end: int, avail: Availability, schedule: Schedule, study: Study):
        # validate scheduler permissions
        if getattr(scheduler, 'is_schedule_assistant', False):
            raise ValueError('Scheduler is not a schedule assistant')

        # validate recipient availability
        if not AvailabilityService.is_available_for_interval(avail, day_index, start, end, recipient):
            raise ValueError('Recipient is not available for the given interval')

        # validate recipient does not have a study scheduled in this interval
        if ScheduleService.study_is_scheduled(schedule, day_index, start, end, recipient):
            raise ValueError('Recipient already has a study scheduled in this interval')

        # schedule the study
        ScheduleService.set_study_for_slot(schedule, day_index, start, end, recipient, study)
