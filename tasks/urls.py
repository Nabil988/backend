from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TaskViewSet,
    event_list_create,
    dashboard_stats,
    calendar_tasks,
    insights_data,
    task_stats_view, 
)

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="tasks")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", dashboard_stats, name="dashboard"),
    path("calendar/", calendar_tasks, name="calendar-tasks"),
    path("insights/", insights_data, name="insights"),
    path("events/", event_list_create, name="event-list-create"),
    path("task-stats/", task_stats_view, name="task-stats"),
]
