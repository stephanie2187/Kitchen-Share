from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta
from django.urls import reverse

from .models import UserModeration, ModerationType, is_librarian, is_patron, get_user_role
from .forms import ModerationForm, UserSearchForm
from form.models import ItemRequest, IssueReport
from users.models import PatronRating
from inventory.models import BorrowRequest

def is_moderator(user):
    return user.is_superuser or is_librarian(user)

@login_required
@user_passes_test(is_moderator)
def user_moderation_list(request):
    users = User.objects.exclude(id=request.user.id)
    form = UserSearchForm(request.GET)

    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        role_filter = form.cleaned_data.get('role_filter')
        status_filter = form.cleaned_data.get('status_filter')

        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        if role_filter:
            if role_filter == 'librarian':
                users = users.filter(groups__name='Librarian')
            elif role_filter == 'patron':
                users = users.filter(groups__name='Patron')

        if status_filter:
            if status_filter == 'active':
                users = users.exclude(
                    moderations__is_active=True
                ).distinct()
            else:
                users = users.filter(
                    moderations__type=status_filter,
                    moderations__is_active=True
                ).distinct()

    for user in users:
        user.role = get_user_role(user)
        user.active_moderation = UserModeration.objects.filter(
            user=user,
            is_active=True
        ).order_by('-created_at').first()

        user.borrow_count = BorrowRequest.objects.filter(patron=user).count()
        user.request_count = ItemRequest.objects.filter(user=user).count()
        user.report_count = IssueReport.objects.filter(user=user).count()

        rating_qs = PatronRating.objects.filter(patron=user)
        user.rating_count = rating_qs.count()
        user.rating_avg = rating_qs.aggregate(avg=Avg('rating'))['avg'] or 0

    context = {
        'users': users,
        'form': form,
        'is_superuser': request.user.is_superuser
    }
    return render(request, 'user_moderation/user_list.html', context)

@login_required
@user_passes_test(is_moderator)
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user_role = get_user_role(user)

    can_moderate = True
    if is_librarian(user) and not request.user.is_superuser:
        can_moderate = False
    if is_librarian(request.user) and user.is_superuser:
        can_moderate = False

    moderation_history = UserModeration.objects.filter(user=user).order_by('-created_at')
    item_requests = ItemRequest.objects.filter(user=user).order_by('-submitted_at')[:10]
    issue_reports = IssueReport.objects.filter(user=user).order_by('-submitted_at')[:10]
    borrow_requests = BorrowRequest.objects.filter(patron=user).order_by('-request_date')[:10]

    active_moderation = UserModeration.objects.filter(
        user=user,
        is_active=True
    ).order_by('-created_at').first()

    if active_moderation:
        print(f"Active moderation found: type={active_moderation.type}, is_active={active_moderation.is_active}")
    else:
        print("No active moderation found")

    if request.method == 'POST':
        form = ModerationForm(
            request.POST,
            moderator=request.user,
            user_to_moderate=user
        )

        if form.is_valid():
            moderation_type = form.cleaned_data['type']
            reason = form.cleaned_data['reason']
            duration_days = form.cleaned_data.get('duration_days')

            UserModeration.objects.filter(
                user=user,
                is_active=True
            ).update(is_active=False)

            moderation = UserModeration(
                user=user,
                type=moderation_type,
                reason=reason,
                created_by=request.user
            )

            if moderation_type == ModerationType.SUSPENSION and duration_days:
                moderation.expires_at = timezone.now() + timedelta(days=duration_days)

            moderation.save()

            messages.success(request, f"User {user.username} has been {moderation.get_type_display().lower()}.")
            return redirect('user_detail', user_id=user.id)
    else:
        form = ModerationForm(
            moderator=request.user,
            user_to_moderate=user
        )

    rating_qs = PatronRating.objects.filter(patron=user)
    user_ratings = {
        'implemented': True,
        'average': rating_qs.aggregate(avg=Avg('rating'))['avg'] or 0,
        'count': rating_qs.count()
    }

    context = {
        'user_profile': user,
        'user_role': user_role,
        'form': form,
        'moderation_history': moderation_history,
        'item_requests': item_requests,
        'issue_reports': issue_reports,
        'borrow_requests': borrow_requests,
        'active_moderation': active_moderation,
        'can_moderate': can_moderate,
        'user_ratings': user_ratings,
        'is_superuser': request.user.is_superuser,
    }

    return render(request, 'user_moderation/user_detail.html', context)

@login_required
def moderation_suspended(request):
    active_suspension = UserModeration.objects.filter(
        user=request.user,
        type=ModerationType.SUSPENSION,
        is_active=True
    ).first()

    if not active_suspension:
        return redirect('home')

    return render(request, 'user_moderation/suspended.html', {'moderation': active_suspension})

@login_required
def moderation_banned(request):
    active_ban = UserModeration.objects.filter(
        user=request.user,
        type=ModerationType.BAN,
        is_active=True
    ).first()

    if not active_ban:
        return redirect('home')

    return render(request, 'user_moderation/banned.html', {'moderation': active_ban})

@login_required
@user_passes_test(is_moderator)
def remove_moderation(request, moderation_id):
    moderation = get_object_or_404(UserModeration, id=moderation_id)
    user = moderation.user

    if moderation.removed_at:
        messages.warning(request, "This moderation action has already been removed.")
        return redirect('user_detail', user_id=user.id)

    if is_librarian(request.user) and not request.user.is_superuser:
        if is_librarian(user) or user.is_superuser:
            messages.error(request, "You don't have permission to remove this moderation.")
            return redirect('user_detail', user_id=user.id)

    if request.method == 'POST':
        removal_reason = request.POST.get('removal_reason', '')
        moderation.remove(removed_by=request.user, reason=removal_reason)
        action_type = moderation.get_type_display().lower()
        messages.success(request, f"The {action_type} has been successfully removed.")
        return redirect('user_detail', user_id=user.id)

    return render(request, 'user_moderation/remove_confirmation.html', {
        'moderation': moderation,
        'user_profile': user,
    })

@login_required
def dismiss_warning(request, warning_id):
    warning = get_object_or_404(UserModeration, id=warning_id, user=request.user, type=ModerationType.WARNING)

    if warning.is_active:
        request.session[f'warning_{warning_id}_dismissed'] = True
        request.session.modified = True
        messages.success(request, "Warning acknowledged.")

    return redirect(request.META.get('HTTP_REFERER', 'home'))
