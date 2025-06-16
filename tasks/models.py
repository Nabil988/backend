from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Task(models.Model):
    """
    Model representing a task assigned to a user, with priority, status, due dates, and completion tracking.
    """
    PRIORITY_CHOICES = [
        ('H', 'High'),
        ('M', 'Medium'),
        ('L', 'Low'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'due_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Ensure consistency between completed boolean and status field.
        if self.completed and self.status != 'completed':
            self.status = 'completed'
        elif not self.completed and self.status == 'completed':
            self.status = 'pending'
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        # True if due_date is in past and task not completed
        return self.due_date and self.due_date < timezone.now() and not self.completed

    @property
    def is_upcoming(self):
        # True if due_date is in future (or now) and task not completed
        return self.due_date and self.due_date >= timezone.now() and not self.completed

    def get_priority_label(self):
        """
        Returns the display label for the priority, or 'Unknown' if invalid.
        """
        priority_dict = dict(self.PRIORITY_CHOICES)
        return priority_dict.get(self.priority, "Unknown")


class Event(models.Model):
    """
    Model representing a calendar event for a user with start/end time and optional all-day flag.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    all_day = models.BooleanField(default=False)

    class Meta:
        ordering = ['start']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        indexes = [
            models.Index(fields=['user', 'start']),
        ]

    def __str__(self):
        start_str = self.start.strftime('%Y-%m-%d %H:%M')
        end_str = self.end.strftime('%H:%M')
        return f"{self.title} ({start_str} - {end_str})"
