from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import ItemForm, CollectionForm
from .models import Collection, Item, BorrowRequest, Rating, Comment, CollectionAccessRequest
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ItemForm, CollectionForm
from users.models import PatronRating
from form.models import ItemRequest
from django.db.models import Q
from datetime import date
import boto3
from django.contrib.auth.models import User
from django.conf import settings

# Helper function to check if user is a librarian
def is_librarian(user):
    return user.groups.filter(name="Librarian").exists()

# Create your views here.
def add_item(request):
    if request.method == "POST":
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():

            item = form.save(commit=False)
            item.uploader = request.user
            item.save()

            return redirect('home')  #redirect user back to home

            #return redirect('/')  #redirect user back to index (home)
    else:
        form = ItemForm()
    return render(request, 'inventory/add_item.html', {'form': form})

@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    if item.uploader != request.user:
        return redirect('home')

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ItemForm(instance=item)

    borrow_history = BorrowRequest.objects.filter(item=item, returned=True)

    for borrow in borrow_history:
        borrow.patron_rating = PatronRating.objects.filter(
            patron=borrow.patron,
            librarian=request.user
        ).first()

    return render(request, 'inventory/edit_item.html', {
        'form': form,
        'item': item,
        'borrow_history': borrow_history
    })


@login_required
def my_borrows(request):
    print("IN MY BORROWS AND MY ITEMS")
    user = request.user

    borrow_requests = BorrowRequest.objects.filter(
        patron=user,
        returned=False
    ).filter(
        Q(status__iexact="approved") | Q(status__iexact="accepted")
    )

    item_requests = ItemRequest.objects.filter(
        user=user,
        returned=False
    ).filter(
        Q(status__iexact="approved") | Q(status__iexact="accepted")
    )

    returned_borrow_requests = BorrowRequest.objects.filter(
        patron=user,
        returned=True
    )

    returned_item_requests = ItemRequest.objects.filter(
        user=user,
        returned=True
    )

    today = date.today()
    notices = []

    for borrow in borrow_requests:
        #print("BORROW:", borrow, "IS NOW TRUE")
        #borrow.is_seen = True
        borrow.is_overdue = borrow.due_date and borrow.due_date < today
        if borrow.due_date:
            time_until_due = (borrow.due_date - today).days
            if time_until_due == 2:
                notices.append({
                    "item": borrow.item,
                    "due_in_48_hours": True,
                    "due_in_24_hours": False,
                    "overdue": False,
                    "due_date": borrow.due_date,
                })
            elif time_until_due == 1:
                notices.append({
                    "item": borrow.item,
                    "due_in_48_hours": False,
                    "due_in_24_hours": True,
                    "overdue": False,
                    "due_date": borrow.due_date,
                })
            elif time_until_due == 0:
                notices.append({
                    "item": borrow.item,
                    "due_in_48_hours": False,
                    "due_in_24_hours": False,
                    "due_today": True,
                    "overdue": False,
                    "due_date": borrow.due_date,
                })
            elif time_until_due < 0:
                notices.append({
                    "item": borrow.item,
                    "due_in_48_hours": False,
                    "due_in_24_hours": False,
                    "due_today": False,
                    "overdue": True,
                    "due_date": borrow.due_date,
                })

    for item in item_requests:
        #print("ITEM:", item, "IS NOW TRUE")
        #item.is_seen = True
        item.is_overdue = item.due_date and item.due_date < today
        if item.due_date:
            time_until_due = (item.due_date - today).days
            if time_until_due == 2:
                notices.append({
                    "item": item.item_name,
                    "due_in_48_hours": True,
                    "due_in_24_hours": False,
                    "due_today": False,
                    "overdue": False,
                    "due_date": item.due_date,
                })
            elif time_until_due == 1:
                notices.append({
                    "item": item.item_name,
                    "due_in_48_hours": False,
                    "due_in_24_hours": True,
                    "due_today": False,
                    "overdue": False,
                    "due_date": item.due_date,
                })
            elif time_until_due == 0:
                notices.append({
                    "item": item.item_name,
                    "due_in_48_hours": False,
                    "due_in_24_hours": False,
                    "due_today": True,
                    "overdue": False,
                    "due_date": item.due_date,
                })
            elif time_until_due < 0:
                notices.append({
                    "item": item.item_name,
                    "due_in_48_hours": False,
                    "due_in_24_hours": False,
                    "due_today": False,
                    "overdue": True,
                    "due_date": item.due_date,
                })

    BorrowRequest.objects.filter(
        patron=user,
        status__in=['approved', 'denied'],
        is_seen_by_patron=False
    ).update(is_seen_by_patron=True)

    ItemRequest.objects.filter(
        user=user,
        status__in=['approved', 'denied'],
        is_seen_by_patron=False
    ).update(is_seen_by_patron=True)

    borrows = list(borrow_requests) + list(item_requests)
    borrow_history = list(returned_borrow_requests) + list(returned_item_requests)

    # for borrow in borrows:
    #     borrow.is_seen = True
    #     borrow.save()


    # for borrow in borrow_history:
    #     borrow.is_seen = True
    #     borrow.save()

    context = {
        'borrows': borrows,
        'borrow_history': borrow_history,
        'today': today,
        'notices': notices,
    }

    return render(request, 'inventory/my_borrows.html', context)


@login_required
def create_collection(request):
    user = request.user
    #checking if user has perms
    if not user: #IF USER DOES NOT EXIST:
        print("User:", user, "has no profile!")
        return redirect('../collections/')
    if user.groups.filter(name="Librarian").exists():
        print("USER HAS ROLE LIBRARIAN")
        role = "Librarian"
    elif user.groups.filter(name="Patron").exists():
        print("USER HAS ROLE PATRON")
        role = "Patron"
    if not role: #NO ROLE ASSIGNED
        print("USER", user, "has no role!")
        return redirect('../collections/')
    if request.method == "POST":
        form = CollectionForm(request.POST, role=role)
        if form.is_valid():
            if request.user.groups.filter(name="Patron").exists() and form.cleaned_data.get("is_private"):
                form.add_error("is_private", "Patrons cannot create private collections.")
                return render(request, 'collections/create_collection.html', {'form': form})
            
            collection = form.save(commit=False)
            collection.created_by = request.user
            collection.save()
            form.save_m2m()
            return redirect('../collections/')
    else:
        form = CollectionForm(request.POST, role=role)
    return render(request, 'collections/create_collection.html', {'form': form})


def collection_list(request):
    search_query = request.GET.get("search", "")
    user = request.user
    all_collections = Collection.objects.all()
    search_query = request.GET.get("search", "").strip().lower()
    #print("SEARCH:", search_query)
    if search_query:
        all_collections = all_collections.filter(
            Q(title__icontains=search_query)
        ).distinct()

    collections = []
    for col in all_collections:
        if col.is_private:
            if user.is_authenticated and (
                col.allowed_users.filter(id=user.id).exists() or
                col.created_by == user or
                user.groups.filter(name="Librarian").exists()
            ):
                has_access = True
            else:
                has_access = False
        else:
            has_access = True

        # Check if user has already requested access
        has_requested = False
        if user.is_authenticated:
            has_requested = CollectionAccessRequest.objects.filter(
                collection=col, user=user
            ).exclude(status='denied').exists()

        collections.append({
            'collection': col,
            'has_access': has_access,
            'has_requested': has_requested
        })

    if user.is_authenticated:
        CollectionAccessRequest.objects.filter(
            user=user,
            status__in=['approved', 'denied'],
            is_seen_by_patron=False
        ).update(is_seen_by_patron=True)

    return render(request, 'collections/collection_list.html', {
        'collections': collections
    })

def item_list(request):
    search_query = request.GET.get("search", "")
    category_filter = request.GET.get("category", "")
    location_filter = request.GET.get("location", "")

    items = Item.objects.filter(
        Q(collections__isnull=True) | Q(collections__is_private=False)
    ).distinct()

    if search_query:
        items = items.filter(title__icontains=search_query)
    if category_filter:
        items = items.filter(category__iexact=category_filter)
    if location_filter:
        items = items.filter(location__iexact=location_filter)

    # Get all unique locations for the dropdown
    all_locations = (
        Item.objects.exclude(location__isnull=True)
        .exclude(location__exact="")
        .values_list("location", flat=True)
        .distinct()
        .order_by("location")
    )

    return render(
        request,
        "inventory/item_list.html",
        {
            "items": items,
            "all_locations": all_locations,
            "location_filter": location_filter,
            "category_filter": category_filter,
            "search_query": search_query,
        },
    )


@login_required
def request_borrow(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    existing_request = BorrowRequest.objects.filter(
        patron=request.user,
        item=item,
        status="pending"
    ).exists()

    creator = item.uploader
    #print("EXISTING REQUEST:", existing_request)
    if existing_request:
        messages.warning(request, "You already placed a request for this item.")
    else:
        BorrowRequest.objects.create(patron=request.user, item=item, status="pending", librarian=creator)
        messages.success(request, "Request placed!")
    
    item.is_seen_by_patron = False
    item.is_seen_by_librarian = False
    item.save()
    return redirect('home')

@login_required
def edit_collection(request, collection_id):
    user = request.user

    # Role detection
    role = None
    if user.groups.filter(name="Librarian").exists():
        print("USER HAS ROLE LIBRARIAN")
        role = "Librarian"
    elif user.groups.filter(name="Patron").exists():
        print("USER HAS ROLE PATRON")
        role = "Patron"

    if not role:
        print("USER", user, "has no role!")
        return redirect('../collections/')

    collection = get_object_or_404(Collection, id=collection_id)

    if request.method == 'POST':
        form = CollectionForm(request.POST, instance=collection, role=role)
        if form.is_valid():
            form.save()
            return redirect('collection_list')
    else:
        form = CollectionForm(role=role, instance=collection)

    # Access management additions (for librarians on private collections)
    access_requests = []
    approved_users = []
    if role == "Librarian" and collection.is_private:
        access_requests = CollectionAccessRequest.objects.filter(
            collection=collection,
            status='pending'
        ).order_by('-request_date')

        approved_users = collection.allowed_users.all()

    return render(request, 'collections/edit_collection.html', {
        'form': form,
        'collection': collection,
        'access_requests': access_requests,
        'approved_users': approved_users
    })

@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)
    user = request.user

    if not user: #IF USER DOES NOT EXIST:
        print("User:", user, "has no profile!")
        return redirect('../collections/')
    if user.groups.filter(name="Librarian").exists():
        print("USER HAS ROLE LIBRARIAN")
        role = "Librarian"
    elif user.groups.filter(name="Patron").exists():
        print("USER HAS ROLE PATRON")
        role = "Patron"
    if not role: #NO ROLE ASSIGNED
        print("USER", user, "has no role!")
        return redirect('../collections/')
    # if not user or not hasattr(user, 'profile'):
    #     print("User:", user, "has no profile!")
    #     return redirect('../collections/')
    # if not user.profile.role:
    #     print("User:", user, "has no role!")
    #     return redirect('../collections/')
    
    if request.method == 'POST':
        if collection.created_by != request.user and not user.groups.filter(name="Librarian").exists():
            return HttpResponseForbidden("You are not allowed to delete this collection.")
        collection.delete()

    return redirect('collection_list')

def item_page(request, item_id):
    item = get_object_or_404(Item, id=item_id)

    role = None
    if request.user.is_authenticated:
        if request.user.groups.filter(name="Librarian").exists():
            role = "Librarian"
        elif request.user.groups.filter(name="Patron").exists():
            role = "Patron"

    active_borrow_exists = BorrowRequest.objects.filter(
        item=item,
        status="approved",
        returned=False
    ).exists()

    if active_borrow_exists:
        item.display_status = "In Circulation"
    else:
        if item.status.lower() in ["returned", "checked in"]:
            item.display_status = "Checked In"
        else:
            item.display_status = item.status

    return render(request, 'item_page.html', {
        'item': item,
        'role': role
    })

@login_required
def return_item(request, pk):

    borrow = BorrowRequest.objects.filter(pk=pk, patron=request.user, returned=False).first()
    if borrow:
        borrow.returned = True
        borrow.status = "returned"
        now = timezone.now()
        borrow.returned_at = now
        borrow.is_seen_by_patron = False
        borrow.save()
        if hasattr(borrow, 'item') and borrow.item:
            borrow.item.status = "returned"
            borrow.item.save()
        return redirect('my_borrows')


    item_req = ItemRequest.objects.filter(pk=pk, user=request.user, returned=False).first()
    if item_req:
        item_req.returned = True
        item_req.status = "returned"
        now = timezone.now()
        item_req.returned_at = now
        item_req.is_seen_by_patron = False
        item_req.save()
        if hasattr(item_req, 'item') and item_req.item:
            item_req.item.status = "returned"
            item_req.item.save()
        return redirect('my_borrows')

    return redirect('my_borrows')

@login_required
@user_passes_test(is_librarian)
def delete_item(request, item_id):
    """Delete an item and its associated files from S3"""
    item = get_object_or_404(Item, id=item_id)

    if request.method == 'POST':
        # First, delete the associated file from S3 if it exists
        if item.photo:
            try:
                # Initialize S3 client
                s3 = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
                )

                # Extract the key from the file URL/path
                key = item.photo.name

                # Delete the file from S3
                s3.delete_object(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Key=key
                )
            except Exception as e:
                # Log the error but continue with database deletion
                print(f"Error deleting file from S3: {e}")

        # Store the item title for the success message
        item_title = item.title

        # Delete the item from the database
        # This will cascade delete any related BorrowRequests as well
        item.delete()

        messages.success(request, f'Item "{item_title}" has been deleted.')
        return redirect('home')

    # If not a POST request, redirect back to the item page
    return redirect('item_page', item_id=item_id)

@login_required
def add_rating(request, item_id):
    item = Item.objects.get(id=item_id)
    if request.method == 'POST':
        rating_value = int(request.POST.get('rating'))
        Rating.objects.create(item=item, user=request.user, rating=rating_value)
    return redirect('item_page', item_id=item.id)

@login_required
def add_comment(request, item_id):
    item = Item.objects.get(id=item_id)
    if request.method == 'POST':
        comment_content = request.POST.get('comment')
        Comment.objects.create(item=item, user=request.user, content=comment_content)
    return redirect('item_page', item_id=item.id)



@login_required
def request_collection_access(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if request.method == 'POST':
        existing_request = CollectionAccessRequest.objects.filter(
            collection=collection,
            user=request.user
        ).first()

        if existing_request:
            if existing_request.status == 'denied':
                # Allow re-request by resetting to pending
                existing_request.status = 'pending'
                existing_request.request_date = timezone.now()
                existing_request.save()
        else:
            CollectionAccessRequest.objects.create(
                collection=collection,
                user=request.user,
                status='pending'
            )

    return redirect('collection_list')


@login_required
@user_passes_test(is_librarian)
def manage_collection_access(request, collection_id):
    collection = get_object_or_404(Collection, id=collection_id)

    if not collection.is_private:
        return redirect('collection_list')  # Only private collections need management

    requests = CollectionAccessRequest.objects.filter(collection=collection).order_by('-request_date')

    return render(request, 'collections/manage_access.html', {
        'collection': collection,
        'requests': requests
    })


@login_required
@user_passes_test(is_librarian)
def handle_access_request(request, request_id, action):
    access_request = get_object_or_404(CollectionAccessRequest, id=request_id)
    access_request.is_seen_by_librarian = True
    access_request.save()
    
    if action == 'approve':
        access_request.status = 'approved'
        access_request.collection.allowed_users.add(access_request.user)
    elif action == 'deny':
        access_request.status = 'denied'
    
    access_request.save()
    return redirect('edit_collection', collection_id=access_request.collection.id)


@login_required
@user_passes_test(is_librarian)
def remove_access(request, collection_id, user_id):
    collection = get_object_or_404(Collection, id=collection_id)
    
    if request.method == "POST":
        user_to_remove = get_object_or_404(User, id=user_id)
        collection.allowed_users.remove(user_to_remove)
    
    return redirect('edit_collection', collection_id=collection.id)

@login_required
def unread_notifications(request):
    user = request.user

    borrow_count = 0
    access_count = 0
    librarian_borrow_count = 0
    librarian_access_count = 0

    if user.groups.filter(name="Patron").exists():
        #print("IN PATRION CHECK")
        borrow_count = BorrowRequest.objects.filter(
            patron=user,
            status__in=['approved', 'denied'],
            is_seen_by_patron=False
        ).count()

        access_count = CollectionAccessRequest.objects.filter(
            user=user,
            status__in=['approved', 'denied'],
            is_seen_by_patron=False
        ).count()

    if user.groups.filter(name="Librarian").exists():
        #print("IN THIS LIBRARIAN CHECK")

        borrow_requests = BorrowRequest.objects.filter(status='pending')
        #for borrow in borrow_requests:
        print("LIBRARIAN BORROW:", borrow_requests)

        librarian_borrow_count = BorrowRequest.objects.filter(
            librarian=user,
            status='pending',
            is_seen_by_librarian=False
        ).distinct().count()

        librarian_access_count = CollectionAccessRequest.objects.filter(
            collection__created_by=user,
            status='pending',
            is_seen_by_librarian=False
        ).count()

    print("TRIGGERED NOTIFS:", user)
    print("BORROWS:", borrow_count)
    print("ACCESS:", access_count)
    print("LIBRARIAN BORROWS:", librarian_borrow_count)
    print("LIBRARIAN ACCESS:", librarian_access_count)

    return JsonResponse({
        'borrow_unread': borrow_count,
        'access_unread': access_count,
        'librarian_borrow_unread': librarian_borrow_count,
        'librarian_access_unread': librarian_access_count,
        'total_unread': borrow_count + access_count + librarian_borrow_count + librarian_access_count
    })