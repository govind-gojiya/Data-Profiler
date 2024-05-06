from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class User(AbstractUser):
    email = models.EmailField(unique=True)
    profile_photo = models.FileField(upload_to='profile_photos/', default='profile_photos/default.jpg', max_length=255)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"Name: {self.username}, ID: {self.id}"
    
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

class EmailAuthBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            User = get_user_model()
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

class Group(models.Model):
    ORGANIZATION = 1
    GROUP = 2
    GROUP_TYPES = (
        (ORGANIZATION, 'Organization'),
        (GROUP, 'Group'),
    )
    
    group_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    group_type = models.SmallIntegerField(choices=GROUP_TYPES, default=GROUP)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_groups')

    def __str__(self):
        return f"Name: {self.name}, ID: {self.group_id}"

class Member(models.Model):
    PENDING = 1
    APPROVED = 2
    REJECTED = 3
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    )

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='memberships')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=PENDING)
    permissions = models.IntegerField()

    def __str__(self):
        return f"user: {self.user}, group: {self.group}"
