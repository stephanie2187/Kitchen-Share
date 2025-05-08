from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.models import User, Group
from inventory.models import Item, BorrowRequest
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import UserProfile, PatronRating
from .forms import ProfilePhotoForm, PatronRatingForm
from inventory.models import Item, BorrowRequest
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseBadRequest

# Create your views here.
def home(request):
    search_query = request.GET.get("search", "")
    category_filter = request.GET.get("category", "")
    sort_option = request.GET.get("sort", "latest")
    location_filter = request.GET.get("location", "")

    role = None
    if request.user.groups.filter(name="Librarian").exists():
        available_items = Item.objects.all()
        role = "Librarian"
    elif request.user.groups.filter(name="Patron").exists():
        available_items = Item.objects.filter(
            Q(collections__isnull=True)
            | Q(collections__is_private=False)
            | Q(collections__allowed_users=request.user)
        ).distinct()
        role = "Patron"

    user_requested_items = BorrowRequest.objects.filter(
        patron=request.user
    ).values_list('item_id', flat=True)

    approved_item_ids = BorrowRequest.objects.filter(
        status="approved"
    ).values_list('item_id', flat=True)

    if request.user.is_authenticated:
        available_items = Item.objects.all()
    else:
        available_items = Item.objects.filter(
            Q(collection__isnull=True) | Q(collection__is_private=False)
        ).distinct()

    if search_query:
        available_items = available_items.filter(title__icontains=search_query)

    if category_filter:
        available_items = available_items.filter(category=category_filter)

    if location_filter:
        available_items = available_items.filter(location=location_filter)

    if sort_option == "latest":
        available_items = available_items.order_by("-published_date")
    elif sort_option == "earliest":
        available_items = available_items.order_by("published_date")

    all_locations = (
        Item.objects.exclude(location__isnull=True)
        .exclude(location__exact="")
        .values_list("location", flat=True)
        .distinct()
        .order_by("location")
    )

    

    borrow_requests = BorrowRequest.objects.filter(patron=request.user)
    borrow_request_status = {
        request.item.id: request.status for request in borrow_requests
    }

    for item in available_items:
        item.borrow_status = borrow_request_status.get(item.id)

    return render(request, 'users/home.html', {
        'items': available_items,
        'user_requested_items': list(user_requested_items),
        'approved_item_ids': list(approved_item_ids),
        'role': role,
        'display_dashboard': True,
        'all_locations': all_locations,
        'location_filter': location_filter,
    })

def login(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, "users/login.html")


def logout_view(request):
    if "current_role" in request.session:
        del request.session["current_role"]
    logout(request)
    request.session.flush()
    return redirect("/")

def assign_patron_role(request):
    user = request.user
    if user.is_authenticated:
        # Check if the user already has a role assigned
        if user.groups.exists():
            if user.groups.filter(name="Librarian").exists():
                from django.contrib.auth import logout
                logout(request)
                # Redirect the user to the login page with error parameter
                return redirect('/login/?error=role_conflict_librarian')
        else:
            patron_group, _ = Group.objects.get_or_create(name="Patron")
            user.groups.add(patron_group)
            request.session["current_role"] = "Patron"
    return redirect("/")

def assign_librarian_role(request):
    user = request.user
    if user.is_authenticated:
        # Check if the user already has a role assigned
        if user.groups.exists():
            if user.groups.filter(name="Patron").exists():
                from django.contrib.auth import logout
                logout(request)
                # Redirect the user to the login page with error parameter
                return redirect('/login/?error=role_conflict_patron')
        else:
            librarian_group, _ = Group.objects.get_or_create(name="Librarian")
            user.groups.add(librarian_group)
            request.session["current_role"] = "Librarian"
    return redirect("/")

@login_required
def profile_info(request):
    user = request.user
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
        messages.info(request, "Profile has been created. You can now update your details.")

    received_ratings = PatronRating.objects.filter(patron=user).order_by('-created_at')
    email_verified = EmailAddress.objects.filter(user=user, verified=True).exists()
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    role = None
    if user.groups.filter(name="Librarian").exists():
        role = "Librarian"
    elif user.groups.filter(name="Patron").exists():
         role = "Patron"

    context = {
            "user": user,
            "username": username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": role,
            "email_verified": email_verified,
            "profile_picture_url": profile.profile_picture.url if profile.profile_picture else None,
            "received_ratings": received_ratings,
    }

    return render(request, "account/profile_info.html", context)

@login_required
def send_identity_verification_email(request):
    if request.method == 'POST':
        user = request.user
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(str(user.pk).encode())
        if settings.DEBUG:
            domain = 'http://127.0.0.1:8000'
        else:
            domain = 'https://project-b-21-sp25-40320f80311d.herokuapp.com'

        verification_link = f"{domain}/verify/{uid}/{token}/"

        subject = "Verify your identity"
        message = f"""
            Hello {user.first_name},

            Click the link below to verify your identity:
            {verification_link}

            If you did not request this verification, please ignore this email.
        """

        send_mail(
            subject,
            message,
            'kitchenshare3250@gmail.com',
            [user.email],
            fail_silently=False,
        )
        return redirect('profile_info')

def verify_identity(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = get_user_model().objects.get(pk=uid)
        print(default_token_generator.check_token(user, token))
        if default_token_generator.check_token(user, token):
            user.profile.is_verified = True
            print(user.profile.is_verified)
            user.profile.save()
            messages.success(request, "Your email has been verified successfully!")
        else:
            messages.error(request, "The verification link is invalid or has expired. Try Again.")
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return HttpResponseBadRequest('Invalid verification link')

    return redirect('profile_info')


ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']

def is_valid_extension(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_required
def upload_profile_photo(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    upload_error = None

    if request.method == 'POST':
        file = request.FILES.get('profile_picture')
        if not file or not is_valid_extension(file.name):
            upload_error = "Only image files (JPG, PNG, GIF) are allowed."
        else:
            profile.profile_picture = file
            profile.save()
            return redirect('profile_info')

    return render(request, 'account/profile_info.html', {
        'username': request.user.username,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'user': request.user,
        'profile_picture_url': profile.profile_picture.url if profile.profile_picture else None,
        'upload_error': upload_error,
    })

def login_view(request):
    """Show the login page with role selection."""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'account/login.html')

@login_required
def manage_roles(request):
    if not request.user.groups.filter(name="Librarian").exists():
        return HttpResponseForbidden("You are not authorized to view this page.")

    patrons = User.objects.filter(groups__name="Patron")
    librarians = User.objects.filter(groups__name="Librarian").exclude(id=request.user.id)

    return render(request, 'roles/manage_roles.html', {
        'patrons': patrons,
        'librarians': librarians,
    })

@login_required
def promote_user(request, user_id):
    if not request.user.groups.filter(name="Librarian").exists():
        return HttpResponseForbidden("Only librarians can promote users.")

    user = get_object_or_404(User, id=user_id)
    patron_group = Group.objects.get(name="Patron")
    librarian_group = Group.objects.get(name="Librarian")

    user.groups.remove(patron_group)
    user.groups.add(librarian_group)

    return redirect('manage_roles')

@login_required
def demote_user(request, user_id):
    if not request.user.groups.filter(name="Librarian").exists():
        return HttpResponseForbidden("Only librarians can demote users.")

    user = get_object_or_404(User, id=user_id)
    patron_group = Group.objects.get(name="Patron")
    librarian_group = Group.objects.get(name="Librarian")

    user.groups.remove(librarian_group)
    user.groups.add(patron_group)

    return redirect('manage_roles')


def librarian_required(user):
    return user.is_authenticated and user.groups.filter(name="Librarian").exists()



@login_required
@user_passes_test(librarian_required)
def rate_patron(request, patron_id):
    patron = get_object_or_404(User, id=patron_id)
    existing_rating = PatronRating.objects.filter(librarian=request.user, patron=patron).first()

    if request.method == 'POST':
        form = PatronRatingForm(request.POST, instance=existing_rating or None)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.librarian = request.user
            rating.patron = patron
            rating.save()
            return redirect('home')
    else:
        form = PatronRatingForm(instance=existing_rating or None)

    return render(request, 'users/rate_patron.html', {'form': form, 'patron': patron})

