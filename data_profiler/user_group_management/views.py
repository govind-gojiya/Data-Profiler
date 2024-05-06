from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import User, Group, Member
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .forms.registration_form import RegisterForm
from django.db.utils import IntegrityError
from connector.models import Connectiondata
from django.db.models import Count, Case, When, IntegerField
from django.utils import timezone
import os


def signin(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        return redirect('home_page')
    
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        user = authenticate(request, email=email, password=password)

        if user is not None:
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if remember_me: 
                request.session.set_expiry(604800) 
            else:
                request.session.set_expiry(0) 
            messages.success(request, "Login successful.")
            return redirect('home_page')
        else:
            messages.error(request, "Invalid email or password.")
    
    return render(request, 'page-login.html')

def register(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already registered and logged in.")
        return redirect('home_page')
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            profile_photo = request.FILES.get('profile_photo')

            try:
                user = User(username=name, email=email)
                user.set_password(password)
                if profile_photo is not None:
                    save_dir = 'static/profile_photos/'
                    timestamp_str = timezone.now().strftime("%Y%m%d%H%M%S")
                    photo_name = f"{name}_profile_{timestamp_str}." + profile_photo.name.split('.')[-1]
                    
                    with open(os.path.join(save_dir, photo_name), 'wb+') as destination:
                        for chunk in profile_photo.chunks():
                            destination.write(chunk)
                
                    user.profile_photo = "profile_photos/" + photo_name

                user.save()
            except ValueError as e:
                if "alread" in e.args[0]:
                    messages.error(request, "Email alread exists.")
                    return render(request, 'page-register.html', {'form': form})
                elif "must be set" in e.args[0]:
                    messages.error(request, "Email must be set.")
                    return render(request, 'page-register.html', {'form': form})
                else:
                    messages.error(request, "An error occurred while registering.")
                    return render(request, 'page-register.html', {'form': form})
            except IntegrityError as e:
                messages.error(request, "Email alread exists.")
                return render(request, 'page-register.html', {'form': form})
            except Exception as e:
                messages.error(request, "An error occurred while registering.")
                return render(request, 'page-register.html', {'form': form})

            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, "Registration successful.")
            return redirect('home_page')
    else:
        form = RegisterForm()

    return render(request, 'page-register.html', {'form': form})

@login_required
def logout(request):
    auth_logout(request)
    return redirect('login_user') 


@login_required
def profile_page(request):
    user = request.user

    user_organization = Group.objects.filter(group_type=Group.ORGANIZATION, members__user_id=user.id, members__status=Member.APPROVED).first()
    user_groups = Member.objects.filter(user__id=user.id, group__group_type=Group.GROUP, status=Member.APPROVED).select_related('group')

    connectors_details = Connectiondata.objects.aggregate(
        num_personal=Count(
            Case(
                When(Q(publish_status=Connectiondata.PERSONAL) & Q(owner=user), then=1),
                output_field=IntegerField()
            )
        ),
        num_group=Count(
            Case(
                When(Q(publish_status=Connectiondata.GROUP) & Q(publish_to_group__members__user_id=user.id), then=1),
                output_field=IntegerField()
            )
        ),
        num_organization=Count(
            Case(
                When(Q(publish_status=Connectiondata.ORGANIZATION) & Q(publish_to_group__members__user_id=user.id), then=1),
                output_field=IntegerField()
            )
        ),
    )


    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        print(request.FILES.get('profile_photo'))
        profile_photo = request.FILES.get('profile_photo')
        user_profile = User.objects.get(id=request.user.id)  

        if profile_photo is not None:
            save_dir = 'static/profile_photos/'
            old_photo = 'static/' + user.profile_photo.name
            if os.path.exists(old_photo):
                os.remove(old_photo)

            timestamp_str = timezone.now().strftime("%Y%m%d%H%M%S")
            photo_name = f"{username}_profile_{timestamp_str}." + profile_photo.name.split('.')[-1]
            
            with open(os.path.join(save_dir, photo_name), 'wb+') as destination:
                for chunk in profile_photo.chunks():
                    destination.write(chunk)
        
            user_profile.profile_photo = "profile_photos/" + photo_name

        user_profile.username = username
        user_profile.email = email
        user_profile.save()
        user = user_profile
    return render(request, 'page-profile.html', {"user": user, "connectors_details": connectors_details, "user_organization": user_organization, "user_groups": user_groups})


@login_required
def organization(request):
    user_id = request.user.id

    user_organization = Group.objects.filter(group_type=Group.ORGANIZATION).filter(
        Q(members__user_id=user_id) | Q(owner_id=user_id),
        members__status=Member.APPROVED
    ).first()

    context = {}
    if not user_organization:
        context["all_organizations"] = Group.objects.filter(group_type=Group.ORGANIZATION)
        context["requested_organizations"] = Member.objects.filter(
            user__id=user_id,
            group__group_type=Group.ORGANIZATION,
            status=Member.PENDING
        )
    else:
        context["user_organization"] = user_organization
        context["members"] = Member.objects.filter(group=user_organization).exclude(user_id=user_id)
        context["is_owner"] = user_organization.owner_id == user_id
        connections_of_user = Connectiondata.objects.filter(publish_status=Connectiondata.ORGANIZATION, publish_to_group=user_organization).select_related('publish_to_group', 'owner').values('meta_id', 'publish_status', 'database_type', 'database_name', 'publish_to_group__name', 'publish_to_group__owner', 'publish_to_group__owner__username', 'owner__username', 'owner')
        context["connections_of_user"] = connections_of_user

    return render(request, 'page-organization.html', context)

@login_required
def new_organization(request):
    if request.method == "POST":
        user = request.user

        Member.objects.filter(user=user, group__group_type=Group.ORGANIZATION, status=Member.PENDING).delete()

        new_org = Group.objects.create(
            name=request.POST.get('organization_name'),
            description=request.POST.get('organization_desc'),
            owner=user,
            group_type=Group.ORGANIZATION
        )

        Member.objects.create(group=new_org, user=user, status=Member.APPROVED, permissions=1)

        messages.success(request, "New organization added successfully.")
        return redirect('organization_dashboard')

    return render(request, 'page-organization.html')

@login_required
def request_to_join(request):
    if request.method == "POST":
        user = request.user
        group_id = request.POST.get('organization_id')
        
        try:
            if not Member.objects.filter(user=user, group__group_id=group_id, status=Member.PENDING).exists():
                group = Group.objects.get(group_id=group_id)
                Member.objects.create(user=user, group=group, status=Member.PENDING, permissions=2)
                messages.success(request, "Your request to join has been submitted.")
            else:
                messages.info(request, "You have already requested to join this organization.")
        except Group.DoesNotExist:
            messages.error(request, "The selected organization does not exist.")
        return redirect('organization_dashboard')
    else:
        return redirect('organization')

@login_required
def delete_requested_organization(request, id):
    try:
        requested_organization = Member.objects.get(group__group_id=id, user__id=request.user.id, status=Member.PENDING)
        requested_organization.delete()
        messages.success(request, "Requested organization deleted successfully.")
    except Member.DoesNotExist:
        messages.error(request, "Requested organization not found.")
    return redirect('organization_dashboard')

@login_required
def accept_requested_organization(request, id):
    try:
        requested_organization = Member.objects.get(id=id)
        requested_organization.status = Member.APPROVED
        requested_organization.save()

        Member.objects.filter(user=requested_organization.user, group__group_type=Group.ORGANIZATION, status__in=[Member.PENDING, Member.REJECTED]).delete()
    except Member.DoesNotExist:
        messages.error(request, "Request not found.")
    return redirect('organization_dashboard')

@login_required
def reject_requested_organization(request, id):
    try:
        requested_organization = Member.objects.get(id=id)
        requested_organization.status = Member.REJECTED
        requested_organization.save()
    except Member.DoesNotExist:
        messages.error(request, "Request not found.")
    return redirect('organization_dashboard')

@login_required
def group(request):
    user = request.user
    user_groups = Member.objects.filter(user__id=user.id, group__group_type=Group.GROUP).select_related('group')
    groups_ids = [group.group_id for group in user_groups if group.status == Member.APPROVED]
    connections_of_user = Connectiondata.objects.filter(publish_status=Connectiondata.GROUP, publish_to_group__in=groups_ids).select_related('publish_to_group', 'owner').values('meta_id', 'publish_status', 'database_type', 'database_name', 'publish_to_group__name', 'publish_to_group__owner', 'publish_to_group__owner__username', 'owner__username', 'owner')
    return render(request, 'page-group.html', {'user_groups': user_groups, 'user': user, 'connections_of_user': connections_of_user})

@login_required
def new_group(request):
    if request.method == "POST":
        new_group = Group.objects.create(
            name=request.POST['group_name'],
            description=request.POST['group_desc'],
            owner=request.user,
            group_type=Group.GROUP
        )
        Member.objects.create(group=new_group, user=request.user, status=Member.APPROVED, permissions=1)
        return redirect('group')

@login_required
def group_detail(request, id):
    user = request.user
    try:
        group = Group.objects.get(group_id=id)
        members = Member.objects.filter(group=group).exclude(user=user)
        members_of = Member.objects.filter(user=user, group__group_type=Group.ORGANIZATION, status=Member.APPROVED).first()
        user_organization_members = None
        if members_of is not None:
            user_organization_members = Member.objects.filter(group=(members_of.group), status=Member.APPROVED).exclude(user=user)
        if user_organization_members is None:
            messages.warning(request, "You have no members to add in group yet.")
        connections_of_user = Connectiondata.objects.filter(publish_status=Connectiondata.GROUP, publish_to_group=group).select_related('publish_to_group', 'owner').values('meta_id', 'publish_status', 'database_type', 'database_name', 'publish_to_group__name', 'publish_to_group__owner', 'publish_to_group__owner__username', 'owner__username', 'owner')
        return render(request, 'page-group-detail.html', {'group': group, 'members': members, 'user': user, 'user_organization_members': user_organization_members, 'connections_of_user': connections_of_user})
    except Group.DoesNotExist:
        messages.error(request, "Group not found.")
        return redirect('group')

@login_required
def request_group_to_join(request, id):
    if request.method == "POST":
        user = request.user
        try:
            requested_user_id = request.POST["requested_user_id"]
            if Member.objects.filter(user=requested_user_id, group__group_id=id).exists():
                messages.info(request, "Can't request to thoes member which already requested or in group.")
            else:
                try: 
                    group = Group.objects.get(group_id=id)
                except Group.DoesNotExist as e:
                    messages.error(request, "Group not exists!")
                    return redirect('group_details', id=id)
                try: 
                    requested_user = User.objects.get(id=requested_user_id)
                except User.DoesNotExist as e:
                    messages.error(request, "User not exists!")
                    return redirect('group_details', id=id)
                Member.objects.create(user=requested_user, group=group, status=Member.PENDING, permissions=2)
                messages.success(request, "Your request to join the group has been submitted.")
        except Group.DoesNotExist:
            messages.error(request, "Group not found.")
        return redirect('group_detail', id=id)

@login_required
def remove_member(request, id):
    try:
        requested_member = Member.objects.get(id=id)
        group_id = requested_member.group.group_id
        requested_member.delete()
        messages.success(request, "Member removed successfully.")
        return redirect('group_detail', id=group_id)
    except Member.DoesNotExist:
        messages.error(request, "Member not found.")
        return redirect('group_detail', id=group_id)
    
@login_required
def accept_group_request(request, id):
    try:
        requested_group_approve = Member.objects.get(id=id)
        requested_group_approve.status = Member.APPROVED
        requested_group_approve.save()
        messages.info(request, "Accepted request of group.")
    except Member.DoesNotExist:
        messages.error(request, "Request not found.")
    return redirect('group')

@login_required
def reject_group_request(request, id):
    try:
        requested_group_approve = Member.objects.get(id=id)
        requested_group_approve.status = Member.REJECTED
        requested_group_approve.save()
        messages.info(request, "Rejected request of group.")
    except Member.DoesNotExist:
        messages.error(request, "Request not found.")
    return redirect('group')

@login_required
def leave_group(request, group_id):
    try:
        leave_group = Member.objects.get(group__group_id=group_id, user=request.user)
        leave_group.delete()
        messages.info(request, "Leave group successfully.")
    except Member.DoesNotExist:
        messages.error(request, "Related entry not found.")
    return redirect('group')

@login_required
def delete_group(request, group_id):
    try:
        group_detail = Group.objects.get(pk=group_id, owner=request.user)
        group_detail.delete()
        messages.info(request, "Deleted group successfully.")
    except Group.DoesNotExist:
        messages.error(request, "Unauthorize access.")
    return redirect('group')