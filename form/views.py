from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ItemRequestForm, BorrowRequestForm, ReportIssueForm, LibrarianItemRequestForm, LibrarianReportIssueForm, LibrarianBorrowRequestForm
from .models import ItemRequest, IssueReport
from inventory.models import BorrowRequest, Rating
from users.models import PatronRating
from django.db.models import Avg

# Existing submission views updated to save the logged-in user
@login_required
def item_request(request):
    if request.method == 'POST':
        form = ItemRequestForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            messages.success(request, 'Item request submitted successfully!')
            return redirect('form:patron_submission_status')
    else:
        form = ItemRequestForm()
    return render(request, 'form/item_request.html', {'form': form})


@login_required
def report_issue(request):
    if request.method == 'POST':
        form = ReportIssueForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            messages.success(request, 'Issue reported successfully!')
            return redirect('form:patron_submission_status')
    else:
        form = ReportIssueForm()
    return render(request, 'form/report_issue.html', {'form': form})


# Helper to restrict access to librarians
def is_librarian(user):
    return user.is_authenticated and user.groups.filter(name="Librarian").exists()

def librarian_borrow_request_detail(request, pk):
    borrow_request = get_object_or_404(BorrowRequest, pk=pk)
    borrow_request.is_seen_by_librarian = True
    borrow_request.save()

    if request.method == 'POST':
        form = LibrarianBorrowRequestForm(request.POST, instance=borrow_request)
        if form.is_valid():
            updated_request = form.save(commit=False)
            updated_request.librarian = request.user
            updated_request.save()
            return redirect('form:librarian_item_requests')
    else:
        form = LibrarianBorrowRequestForm(instance=borrow_request)

    return render(request, 'form/librarian_borrow_request_detail.html', {
        'borrow_request': borrow_request,
        'form': form,
    })


# Librarian list view for Item Requests
@login_required
@user_passes_test(is_librarian)
def librarian_item_requests(request):
    item_requests = ItemRequest.objects.all().select_related('user')

    borrow_requests = BorrowRequest.objects.filter(
        item__uploader=request.user
    ).select_related('patron', 'item')

    all_requests = list(item_requests) + list(borrow_requests)

    for req in all_requests:
        if isinstance(req, ItemRequest):
            req.request_type = 'ItemRequest'
            patron = req.user
            item = None
            # no item ratings here
            req.item_num_ratings = 0
            req.item_rating = None
        else:
            req.request_type = 'BorrowRequest'
            patron = req.patron
            item = req.item
            item_qs = Rating.objects.filter(item=item)
            avg_ir = item_qs.aggregate(avg=Avg('rating'))['avg']
            req.item_rating = round(avg_ir, 1) if avg_ir is not None else None
            req.item_num_ratings = item_qs.count()

        # Compute patron ratings
        patron_qs = PatronRating.objects.filter(patron=patron)
        avg_pr = patron_qs.aggregate(avg=Avg('rating'))['avg']
        req.patron_rating = round(avg_pr, 1) if avg_pr is not None else None
        req.num_ratings = patron_qs.count()

    return render(request, 'form/librarian_item_requests.html', {
        'requests': all_requests
    })

# Detailed view for a single Item Request (edit/delete/status update)
@login_required
@user_passes_test(is_librarian)
def librarian_item_request_detail(request, pk):
   
    req_obj = ItemRequest.objects.filter(pk=pk).first()

    if req_obj:
        form_class = LibrarianItemRequestForm
        request_type = 'ItemRequest'
    else:
       
        req_obj = BorrowRequest.objects.filter(pk=pk).first()
        if req_obj:
            form_class = LibrarianBorrowRequestForm  
            request_type = 'BorrowRequest'
       

    if request.method == 'POST':
        if 'update' in request.POST:
            form = form_class(request.POST, instance=req_obj)
            if form.is_valid():
                updated_request = form.save(commit=False)
                if isinstance(updated_request, BorrowRequest) and updated_request.status.lower() == "approved":
                    already_approved = BorrowRequest.objects.filter(
                        item=updated_request.item,
                        status__iexact="approved"
                    ).exclude(pk=updated_request.pk).exists()

                    if already_approved:
                        updated_request.status = "Denied"
                        updated_request.librarian = request.user
                        updated_request.save()
                        messages.error(request, "This item has already been approved for another user. This request was automatically denied.")

                    else:
                        updated_request.librarian = request.user
                        updated_request.save()
                       
                        BorrowRequest.objects.filter(
                            item=updated_request.item,
                            status__iexact="pending"
                        ).exclude(pk=updated_request.pk).update(status="Denied")
                        messages.success(request, 'Request approved and all others denied.')
                elif isinstance(updated_request, ItemRequest) and updated_request.status.lower() == "accepted":
                    updated_request.librarian = request.user  
                    
                   
                    updated_request.save()
                    messages.success(request, 'Item request approved and librarian assigned.')
                else:
                    updated_request.save()
                    messages.success(request, 'Request updated successfully.')

        elif 'delete' in request.POST:
            req_obj.delete()
            messages.success(request, 'Request deleted successfully.')
            return redirect('form:librarian_item_requests')
    else:
        form = form_class(instance=req_obj)

    return render(request, 'form/librarian_item_request_detail.html', {
        'form': form,
        'submission': req_obj,
        'request_type': request_type  
    })


# Librarian list view for Issue Reports
@login_required
@user_passes_test(is_librarian)
def librarian_issue_reports(request):
    reports_list = IssueReport.objects.all()
    return render(request, 'form/librarian_issue_reports.html', {'reports': reports_list})


# Detailed view for a single Issue Report (edit/delete/status update)
@login_required
@user_passes_test(is_librarian)
def librarian_issue_report_detail(request, pk):
    report_obj = get_object_or_404(IssueReport, pk=pk)
    if request.method == 'POST':
        if 'update' in request.POST:
            form = LibrarianReportIssueForm(request.POST, instance=report_obj)
            if form.is_valid():
                form.save()
                messages.success(request, 'Issue report updated successfully.')
        elif 'delete' in request.POST:
            report_obj.delete()
            messages.success(request, 'Issue report deleted successfully.')
            return redirect('form:librarian_issue_reports')
    else:
        form = LibrarianReportIssueForm(instance=report_obj)
    return render(request, 'form/librarian_issue_report_detail.html', {'form': form, 'submission': report_obj})


@login_required
def patron_submission_status(request):
    
    item_requests = ItemRequest.objects.filter(user=request.user)
    borrow_requests = BorrowRequest.objects.filter(patron=request.user)
    issue_reports = IssueReport.objects.filter(user=request.user)

    return render(request, 'form/patron_submission_status.html', {
        'item_requests': item_requests,  
        'borrow_requests': borrow_requests,  
        'issue_reports': issue_reports,
    })



# New views for patrons updating their submissions:
@login_required
def patron_item_request_detail(request, pk):
    
    submission = get_object_or_404(ItemRequest, pk=pk, user=request.user)
    is_item_request = True

    if not submission:
        submission = get_object_or_404(BorrowRequest, pk=pk, patron=request.user)
        is_item_request = False

    form_class = ItemRequestForm if is_item_request else BorrowRequestForm

    if request.method == 'POST':
        form = form_class(request.POST, instance=submission)
        if form.is_valid():
            instance = form.save(commit=False)

            if is_item_request:
                instance.status = 'Unreviewed'  

            instance.save()
            messages.success(request, 'Request updated successfully.')
            return redirect('form:patron_submission_status')  
    else:
        form = form_class(instance=submission)

    return render(request, 'form/patron_item_request_detail.html', {
        'form': form,
        'submission': submission
    })


@login_required
def patron_issue_report_detail(request, pk):
    submission = get_object_or_404(IssueReport, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ReportIssueForm(request.POST, instance=submission)
        if form.is_valid():
            instance = form.save(commit=False)
           
            instance.status = 'Unreviewed'
            instance.save()
            messages.success(request, 'Issue report updated successfully.')
            return redirect('form:patron_submission_status')
    else:
        form = ReportIssueForm(instance=submission)
    return render(request, 'form/patron_issue_report_detail.html', {'form': form, 'submission': submission})
    

@login_required
def patron_borrow_request_detail(request, pk):
   
    borrow_request = get_object_or_404(BorrowRequest, pk=pk, patron=request.user)
    
    if request.method == 'POST':
        form = BorrowRequestForm(request.POST, instance=borrow_request)
        if form.is_valid():
            # form.save()
            messages.success(request, 'Borrow request updated successfully.')
            return redirect('form:patron_submission_status')
    else:
        form = BorrowRequestForm(instance=borrow_request)

    return render(request, 'form/patron_borrow_request_detail.html', {
        'form': form,
        'borrow_request': borrow_request  
    })
