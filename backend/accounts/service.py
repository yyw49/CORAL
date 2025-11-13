from accounts.models import Availability, LabAssistant, AvailabilityDay, Schedule, ScheduleDay, Study, Day
from datetime import time

# -------------------------
# Availability Service
# -------------------------
class AvailabilityService:
    SLOTS_PER_DAY = Day.SLOTS_PER_DAY

    @staticmethod
    def create_availability(assistant: LabAssistant) -> Availability:
        """
        Creates a new Availability object for the assistant with 5 AvailabilityDay objects (Mon-Fri)
        """
        days = []
        for i in range(5):
            day_obj = AvailabilityDay.objects.create()
            days.append(day_obj)

        availability = Availability.objects.create(
            lab_assistant=assistant,
            monday=days[0],
            tuesday=days[1],
            wednesday=days[2],
            thursday=days[3],
            friday=days[4],
        )
        return availability

    @staticmethod
    def validate_slot_index(slot_index: int):
        if slot_index < 0 or slot_index >= AvailabilityService.SLOTS_PER_DAY:
            raise ValueError(f"slot_index must be in range [0, {AvailabilityService.SLOTS_PER_DAY-1}]")

    @staticmethod
    def validate_day_index(day_index: int):
        if day_index < 0 or day_index >= 5:
            raise ValueError("day_index must be 0 (Monday) to 4 (Friday)")

    @staticmethod
    def get_day(assistant: LabAssistant, day_index: int) -> AvailabilityDay:
        AvailabilityService.validate_day_index(day_index)
        avail = assistant.availability
        day_name = Availability.DAYS[day_index]
        return getattr(avail, day_name)

    @staticmethod
    def set_slot(assistant: LabAssistant, day_index: int, slot_index: int, available: bool):
        AvailabilityService.validate_slot_index(slot_index)
        day = AvailabilityService.get_day(assistant, day_index)
        day.slots[str(slot_index)] = 1 if available else 0
        day.save(update_fields=['slots'])

    @staticmethod
    def set_interval(assistant: LabAssistant, day_index: int, start: int, end: int, available: bool = True):
        for i in range(start, end):
            AvailabilityService.set_slot(assistant, day_index, i, available)

    @staticmethod
    def is_available(assistant: LabAssistant, day_index: int, start: int, end: int) -> bool:
        day = AvailabilityService.get_day(assistant, day_index)
        return all(day.slots.get(str(i), 0) == 1 for i in range(start, end))

    @staticmethod
    def get_available_intervals(assistant: LabAssistant):
        """
        Returns dict mapping day_index (0=Monday,..,4=Friday)
        to list of (start_slot, end_slot) contiguous intervals where assistant is available
        """
        intervals_per_day = {}
        for day_index in range(5):
            day = AvailabilityService.get_day(assistant, day_index)
            intervals = []
            i = 0
            while i < AvailabilityService.SLOTS_PER_DAY:
                if day.slots.get(str(i), 0) == 1:
                    start = i
                    while i < AvailabilityService.SLOTS_PER_DAY and day.slots.get(str(i), 0) == 1:
                        i += 1
                    intervals.append((start, i))
                else:
                    i += 1
            intervals_per_day[day_index] = intervals
        return intervals_per_day


# -------------------------
# Schedule Service
# -------------------------
class ScheduleService:
    @staticmethod
    def create_schedule(lab_assistant: LabAssistant, start_date) -> Schedule:
        """
        Creates a new schedule for a lab assistant for the week starting at start_date.
        Automatically creates the 5 ScheduleDay objects for Monday-Friday.
        """
        days = []
        for i in range(5):
            day_date = start_date + timedelta(days=i)
            day_obj = ScheduleDay.objects.create(date=day_date)
            days.append(day_obj)

        schedule = Schedule.objects.create(
            lab_assistant=lab_assistant,
            start_date=start_date,
            monday=days[0],
            tuesday=days[1],
            wednesday=days[2],
            thursday=days[3],
            friday=days[4],
        )
        return schedule

    @staticmethod
    def validate_day_index(day_index: int):
        if day_index < 0 or day_index >= 5:
            raise ValueError("day_index must be 0-4")

    @staticmethod
    def get_day(schedule: Schedule, day_index: int) -> ScheduleDay:
        ScheduleService.validate_day_index(day_index)
        day_name = Schedule.DAYS[day_index]
        return getattr(schedule, day_name)

    @staticmethod
    def study_is_scheduled(schedule: Schedule, day_index: int, start: int, end: int) -> bool:
        day = ScheduleService.get_day(schedule, day_index)
        for i in range(start, end):
            if day.slots.get(str(i), -1) != -1:
                return True
        return False

    @staticmethod
    def set_study(schedule: Schedule, day_index: int, start: int, end: int, study: Study):
        day = ScheduleService.get_day(schedule, day_index)
        for i in range(start, end):
            day.slots[str(i)] = study.id
        day.save(update_fields=['slots'])

    @staticmethod
    def clear_study(schedule: Schedule, day_index: int, start: int, end: int):
        day = ScheduleService.get_day(schedule, day_index)
        for i in range(start, end):
            day.slots[str(i)] = -1
        day.save(update_fields=['slots'])

    @staticmethod
    def schedule_study(scheduler: LabAssistant, recipient: LabAssistant, schedule: Schedule, day_index: int, start: int, end: int, study: Study):
        if not getattr(scheduler, 'is_schedule_assistant', False):
            raise ValueError("Scheduler is not a schedule assistant")

        if not AvailabilityService.is_available(recipient, day_index, start, end):
            raise ValueError("Recipient is not available in the selected interval")

        if ScheduleService.study_is_scheduled(schedule, day_index, start, end):
            raise ValueError("Study already scheduled in this interval")

        ScheduleService.set_study(schedule, day_index, start, end, study)

    @staticmethod
    def unschedule_study(scheduler: LabAssistant, schedule: Schedule, day_index: int, start: int, end: int):
        if not getattr(scheduler, 'is_schedule_assistant', False):
            raise ValueError("Scheduler is not a schedule assistant")

        ScheduleService.clear_study(schedule, day_index, start, end)


# -------------------------
# Study Service
# -------------------------
class StudyService:
    @staticmethod
    def create_study(name: str, description: str, creator: LabAssistant) -> Study:
        if not getattr(creator, 'is_schedule_assistant', False):
            raise ValueError("Creator is not a schedule assistant")
        return Study.objects.create(name=name, description=description)

    @staticmethod
    def get_study(study_id: int) -> Study:
        return Study.objects.get(id=study_id)

    @staticmethod
    def update_study(study: Study, name: str, description: str, creator: LabAssistant) -> Study:
        if not getattr(creator, 'is_schedule_assistant', False):
            raise ValueError("Creator is not a schedule assistant")
        study.name = name
        study.description = description
        study.save(update_fields=['name', 'description'])
        return study
