from django.contrib import admin
from .models import Task, Event

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'priority', 'completed', 'due_date', 'created_at')
    list_filter = ('completed', 'status', 'priority', 'due_date', 'created_at')
    search_fields = ('title', 'description', 'user__username', 'user__email')
    ordering = ('-created_at',)
    date_hierarchy = 'due_date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'user', 'status', 'priority', 'completed')
        }),
        ('Dates', {
            'fields': ('due_date', 'created_at', 'updated_at'),
        }),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'start', 'end', 'all_day')
    list_filter = ('all_day', 'start')
    search_fields = ('title', 'description', 'user__username', 'user__email')
    ordering = ('start',)
    date_hierarchy = 'start'
    readonly_fields = ('start', 'end')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'user', 'all_day')
        }),
        ('Event Timing', {
            'fields': ('start', 'end'),
        }),
    )
