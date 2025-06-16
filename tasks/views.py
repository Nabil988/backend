import traceback
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.db.models import Count
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Task, Event
from .serializers import TaskSerializer, EventSerializer

User = get_user_model()

# === Utils ===
def get_user_from_request(request):
    if getattr(settings, "DISABLE_AUTH_FOR_TESTING", False):
        user = User.objects.first()
        if not user:
            raise Exception("No users exist in database for test mode.")
        return user
    return request.user

def get_permission_classes():
    if getattr(settings, "DISABLE_AUTH_FOR_TESTING", False):
        return [permissions.AllowAny()]
    return [permissions.IsAuthenticated()]

# === Auth Views ===
class SafeTokenObtainPairView(TokenObtainPairView):
    http_method_names = ['post']

    def get(self, request, *args, **kwargs):
        return Response({"detail": "Method 'GET' not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_view(request):
    try:
        data = request.data
        username, email, password = data.get("username"), data.get("email"), data.get("password")

        if not all([username, email, password]):
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({"message": "Signup successful.", "username": user.username}, status=status.HTTP_201_CREATED)

    except Exception:
        traceback.print_exc()
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
    except Exception:
        traceback.print_exc()
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def forgot_password_view(request):
    try:
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"message": "If this email exists, a reset link was sent."}, status=status.HTTP_200_OK)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password/{uid}/{token}/"

        send_mail(
            subject="SmartTasker Password Reset",
            message=f"Click here to reset your password:\n{reset_link}",
            from_email="noreply@smarttasker.com",
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"message": "If this email exists, a reset link was sent."}, status=status.HTTP_200_OK)

    except Exception:
        traceback.print_exc()
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def reset_password_view(request, uidb64, token):
    try:
        password = request.data.get("password")
        if not password:
            return Response({"error": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)

        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired reset link."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()

        return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

    except Exception:
        traceback.print_exc()
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# === Task CRUD ===
class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_permissions(self):
        return get_permission_classes()

    def get_queryset(self):
        user = get_user_from_request(self.request)
        return Task.objects.filter(user=user)

    def perform_create(self, serializer):
        user = get_user_from_request(self.request)
        serializer.save(user=user)

# === Events API ===
@api_view(["GET", "POST"])
@permission_classes(get_permission_classes())
def event_list_create(request):
    try:
        user = get_user_from_request(request)

        if request.method == "GET":
            events = Event.objects.filter(user=user)
            serializer = EventSerializer(events, many=True)
            return Response(serializer.data)

        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception:
        traceback.print_exc()
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# === Dashboard Stats ===
@api_view(["GET"])
@permission_classes(get_permission_classes())
def dashboard_stats(request):
    try:
        user = get_user_from_request(request)
        tasks = Task.objects.filter(user=user)

        total = tasks.count()
        completed = tasks.filter(status='completed').count()
        pending = tasks.exclude(status='completed').count()

        now = timezone.now()
        upcoming_tasks = tasks.filter(
            due_date__gt=now,
            due_date__lte=now + timedelta(days=7),
        ).exclude(status='completed')

        upcoming = [
            {
                "id": t.id,
                "title": t.title,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "description": t.description,
            }
            for t in upcoming_tasks
        ]

        return Response({
            "total": total,
            "completed": completed,
            "pending": pending,
            "upcoming": upcoming
        })

    except Exception:
        traceback.print_exc()
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# === Calendar Data ===
@api_view(["GET"])
@permission_classes(get_permission_classes())
def calendar_tasks(request):
    try:
        user = get_user_from_request(request)
        tasks = Task.objects.filter(user=user).exclude(due_date__isnull=True)
        events = [
            {
                "id": t.id,
                "title": t.title,
                "start": t.due_date.isoformat(),
                "end": t.due_date.isoformat(),
                "completed": t.completed,
                "priority": t.get_priority_display(),
                "status": t.get_status_display(),
            }
            for t in tasks
        ]
        return Response(events)

    except Exception:
        traceback.print_exc()
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# === Insights / Task Stats ===
@api_view(["GET"])
@permission_classes(get_permission_classes())
def insights_data(request):
    try:
        user = get_user_from_request(request)

        task_stats = (
            Task.objects.filter(user=user)
            .values("priority")
            .annotate(count=Count("id"))
        )

        priority_map = dict(Task.PRIORITY_CHOICES)

        result = [
            {
                "priority": priority_map.get(item["priority"], "Unknown"),
                "count": item["count"]
            }
            for item in task_stats
        ]

        return Response({"data": result}, status=status.HTTP_200_OK)

    except Exception:
        traceback.print_exc()
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# === Task Statistics: Count by Priority and Completion ===
@api_view(["GET"])
@permission_classes(get_permission_classes())
def task_stats_view(request):
    try:
        user = get_user_from_request(request)
        tasks = Task.objects.filter(user=user)

        stats = {
            "high_priority": tasks.filter(priority="H").count(),
            "medium_priority": tasks.filter(priority="M").count(),
            "low_priority": tasks.filter(priority="L").count(),
            "completed": tasks.filter(status="completed").count(),
            "pending": tasks.exclude(status="completed").count(),
        }

        return Response(stats, status=status.HTTP_200_OK)

    except Exception:
        traceback.print_exc()
        return Response({"error": "Internal server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
