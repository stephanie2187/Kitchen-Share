from django.urls import path
from . import views
from .views import *

urlpatterns = [
    path('add-item/', add_item, name='add_item'),
    path("create-collection/", create_collection, name="create_collection"),
    path('collections/<int:collection_id>/edit/', edit_collection, name='edit_collection'),
    path('collections/<int:collection_id>/delete/', delete_collection, name='delete_collection'),
    path("collections/", collection_list, name="collection_list"),
    path('items/', item_list, name='item_list'),
    path("request/<int:item_id>/", views.request_borrow, name="request_borrow"),
    path('item/<int:item_id>/', item_page, name='item_page'),
    path('item/<int:item_id>/delete/', views.delete_item, name='delete_item'),
    path('my-borrows/', my_borrows, name='my_borrows'),
    path('return/<int:pk>/', views.return_item, name='return_item'),
    path('item/<int:item_id>/edit/', edit_item, name='edit_item'),
    path('item/<int:item_id>/rate/', views.add_rating, name='add_rating'),
    path('item/<int:item_id>/comment/', views.add_comment, name='add_comment'),
    path('collections/request-access/<int:collection_id>/', views.request_collection_access, name='request_collection_access'),
    path('collections/access-request/<int:request_id>/<str:action>/', views.handle_access_request, name='handle_access_request'),
    path('collections/<int:collection_id>/remove-access/<int:user_id>/', views.remove_access, name='remove_access'),
    path('api/unread-notifications/', views.unread_notifications, name='unread_notifications'),
]


