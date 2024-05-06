from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", views.signin, name="login_user"),
    path("login", views.signin, name="login_user"),
    path("register", views.register, name="register_user"),
    path("logout", views.logout, name="logout_user"),
    path("profile", views.profile_page, name="profile_page"),
    path("organization", views.organization, name="organization_dashboard"),
    path("new_organization", views.new_organization, name="create_organization"),
    path('organization/request_to_join/', views.request_to_join, name='request_to_join'),
    path('delete_requested_organization/<int:id>', views.delete_requested_organization, name='delete_requested_organization'),
    path('accept_request/<int:id>', views.accept_requested_organization, name='accept_request'),
    path('reject_request/<int:id>', views.reject_requested_organization, name='reject_request'),
    path('group', views.group, name='group'),
    path('new_group', views.new_group, name='create_group'),
    path('group/<int:id>', views.group_detail, name='group_detail'),
    path('request_group_to_join/<int:id>', views.request_group_to_join, name='request_group_to_join'),
    path('remove_member/<int:id>', views.remove_member, name='remove_member'),
    path('accept_group_request/<int:id>', views.accept_group_request, name='accept_group_request'),
    path('reject_group_request/<int:id>', views.reject_group_request, name='reject_group_request'),
    path('leave_group/<int:group_id>', views.leave_group, name='leave_group'),
    path('delete_group/<int:group_id>', views.delete_group, name='delete_group'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    