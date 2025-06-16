from rest_framework import serializers
from .models import Task, Event
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

User = get_user_model()

# --- Task & Event Serializers ---

class TaskSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'due_date',
            'created_at', 'updated_at', 'completed',
            'priority', 'priority_display',
            'status', 'status_display',
            'is_overdue', 'is_upcoming',
            'user'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context.get('request').user
        validated_data['user'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('user', None)  # Prevent user update
        return super().update(instance, validated_data)


class EventSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'start', 'end', 'all_day', 'user'
        ]
        read_only_fields = ['id', 'user']

    def create(self, validated_data):
        user = self.context.get('request').user
        validated_data['user'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('user', None)  # Prevent user update
        return super().update(instance, validated_data)

# --- Authentication Serializers ---

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'username', 'password']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data.get('username'), password=data.get('password'))
        if user and user.is_active:
            return user
        raise serializers.ValidationError("Invalid login credentials.")


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class ResetPasswordConfirmSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        try:
            uid = force_str(urlsafe_base64_decode(data.get('uidb64')))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            raise serializers.ValidationError("Invalid reset link.")

        if not default_token_generator.check_token(user, data.get('token')):
            raise serializers.ValidationError("Invalid or expired token.")

        data['user'] = user
        return data

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
