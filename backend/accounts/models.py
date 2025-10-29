from django.db import models
from django.contrib.auth.models import User
from datetime import time, timedelta

class LabAssistant(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lab_assistant')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.user.get_full_name()
    
    class Meta:
        verbose_name = 'Lab Assistant'
        verbose_name_plural = 'Lab Assistants'


class Day(models.Model):

    # 32 slots of 15 minutes each across 8 hours (9-5)
    SLOTS_PER_DAY = 32

    # lab_assistant = models.ForeignKey(LabAssistant, on_delete=models.CASCADE, related_name='days')
    # day_of_week = models.IntegerField(choices=DAY_CHOICES)
    def _default_slots():
        # 48 slots, each contains a list of LabAssistant IDs available in that slot
        return [[] for _ in range(Day.SLOTS_PER_DAY)]

    slots = models.JSONField(default=_default_slots)

    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateTimeField()


    # --- Slot helpers (30-minute intervals) ---
    # pull out to clean method
    @staticmethod
    def _validate_slot_index(slot_index: int) -> None:
        if slot_index < 0 or slot_index >= Day.SLOTS_PER_DAY:
            raise ValueError('slot_index must be in range [0, 47]')

    @staticmethod
    def time_to_slot_index(t: time) -> int:
        """Convert a datetime.time to a 0..47 slot index (30-minute buckets)."""
        total_minutes = t.hour * 60 + t.minute
        return min(total_minutes // 30, Day.SLOTS_PER_DAY - 1)

    @staticmethod
    def time_to_slot_index_ceil(t: time) -> int:
        """Convert time to the slot index after snapping up to the next 30-minute boundary."""
        total_minutes = t.hour * 60 + t.minute
        if (total_minutes % 30) != 0:
            total_minutes = min(((total_minutes // 30) + 1) * 30, 24 * 60)
        return min(total_minutes // 30, Day.SLOTS_PER_DAY)

    def get_assistant_ids_for_slot(self, slot_index: int):
        Day._validate_slot_index(slot_index)
        return list(self.slots[slot_index])

    def slot_has_assistant(self, slot_index: int, lab_assistant: LabAssistant) -> bool:
        Day._validate_slot_index(slot_index)
        return int(lab_assistant.id) in self.slots[slot_index]

    def set_slot_for_assistant(self, slot_index: int, lab_assistant: LabAssistant, available: bool) -> None:
        Day._validate_slot_index(slot_index)
        assistant_id = int(lab_assistant.id)
        current_ids = self.slots[slot_index]
        if available:
            if assistant_id not in current_ids:
                current_ids.append(assistant_id)
        else:
            if assistant_id in current_ids:
                current_ids.remove(assistant_id)

    def set_interval_for_assistant(self, start_slot_index: int, end_slot_index: int, lab_assistant: LabAssistant, available: bool = True) -> None:
        """
        Set availability for a half-open interval of slots [start_slot_index, end_slot_index)
        for a specific LabAssistant.
        """
        if start_slot_index < 0 or end_slot_index > Day.SLOTS_PER_DAY or start_slot_index > end_slot_index:
            raise ValueError('Invalid slot interval')
        if start_slot_index == end_slot_index:
            self.set_slot_for_assistant(start_slot_index, lab_assistant)
        for i in range(start_slot_index, end_slot_index):
            self.set_slot_for_assistant(i, lab_assistant, available)

    def clear_all(self) -> None:
        for i in range(Day.SLOTS_PER_DAY):
            self.slots[i] = []

    def set_all_for_assistant(self, lab_assistant: LabAssistant) -> None:
        for i in range(Day.SLOTS_PER_DAY):
            self.set_slot_for_assistant(i, lab_assistant, True)

    def get_available_slot_indices_for_assistant(self, lab_assistant: LabAssistant):
        return [i for i in range(Day.SLOTS_PER_DAY) if self.slot_has_assistant(i, lab_assistant)]

    def get_available_intervals_for_assistant(self, lab_assistant: LabAssistant):
        """
        Returns a list of (start_slot, end_slot) contiguous ranges where the given
        LabAssistant is available.
        """
        intervals = []
        i = 0
        while i < Day.SLOTS_PER_DAY:
            if self.slot_has_assistant(i, lab_assistant):
                start = i
                while i < Day.SLOTS_PER_DAY and self.slot_has_assistant(i, lab_assistant):
                    i += 1
                intervals.append((start, i))
            else:
                i += 1
        return intervals