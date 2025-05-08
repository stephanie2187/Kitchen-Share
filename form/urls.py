from django.urls import path
from . import views

app_name = 'form'

urlpatterns = [
    path('request-item/', views.item_request, name='item_request'),
    path('report-issue/', views.report_issue, name='report_issue'),

    # Librarian pages
    path('librarian/item-requests/', views.librarian_item_requests, name='librarian_item_requests'),
    path('librarian/item-requests/<int:pk>/', views.librarian_item_request_detail, name='librarian_item_request_detail'),
    path('librarian/borrow-requests/<int:pk>/', views.librarian_borrow_request_detail, name='librarian_borrow_request_detail'),
    path('librarian/issue-reports/', views.librarian_issue_reports, name='librarian_issue_reports'),
    path('librarian/issue-reports/<int:pk>/', views.librarian_issue_report_detail, name='librarian_issue_report_detail'),

    # Patron status page and detail updating pages
    path('patron/status/', views.patron_submission_status, name='patron_submission_status'),
    path('patron/item-request/<int:pk>/', views.patron_item_request_detail, name='patron_item_request_detail'),
    path('borrow-request/<int:pk>/', views.patron_borrow_request_detail, name='patron_borrow_request_detail'),
    path('patron/issue-report/<int:pk>/', views.patron_issue_report_detail, name='patron_issue_report_detail'),
]