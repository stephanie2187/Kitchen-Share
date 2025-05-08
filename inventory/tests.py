from django.test import TestCase
from django.contrib.auth.models import User
from inventory.models import Item, Collection, BorrowRequest
from inventory.forms import ItemForm
import random
import string

# Create your tests here.

class ItemModelTest(TestCase):
    def setUp(self):
        """Set up a sample item before each test."""
        self.user = User.objects.create_user(username="testuser", password="testpassword")

        self.item = Item.objects.create(
            title="Test Item",
            description="This is a test item.",
            category="cookware",
            condition="good",
            uploader=self.user
        )

    def test_item_creation(self):
        """Test that an item is created successfully."""
        self.assertEqual(self.item.title, "Test Item")
        self.assertEqual(self.item.category, "cookware")
        self.assertEqual(self.item.condition, "good")

    def test_primary_identifier_is_auto_generated(self):
        """Test that the 'primary_identifier' field is automatically generated."""
        self.assertIsNotNone(self.item.primary_identifier)
        self.assertEqual(len(self.item.primary_identifier), 10)

    def test_primary_identifier_is_unique(self):
        """Test that 'primary_identifier' is unique for each item."""
        another_item = Item.objects.create(
            title="Another Item",
            description="Another test item.",
            category="spices",
            condition="brand_new",
            uploader=self.user
        )
        self.assertNotEqual(self.item.primary_identifier, another_item.primary_identifier)

    def test_invalid_item_form_submission(self):
        """Test submitting an invalid item form (missing title)."""
        form_data = {
            "description": "Missing title.",
            "category": "spices",
            "condition": "good",
        }
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)


class CollectionModelTest(TestCase):
    def setUp(self):
        """Set up a user and a collection before each test."""
        self.user = User.objects.create_user(username="testuser", password="password")
        self.collection = Collection.objects.create(
            title="Test Collection",
            description="A test collection.",
            created_by=self.user
        )

    def test_collection_creation(self):
        """Test that a collection is created successfully."""
        self.assertEqual(self.collection.title, "Test Collection")
        self.assertEqual(self.collection.description, "A test collection.")
        self.assertEqual(self.collection.created_by, self.user)

    def test_add_item_to_collection(self):
        """Test adding an item to a collection."""
        item = Item.objects.create(
            title="Collection Item",
            description="An item to add to the collection.",
            category="cookware",
            condition="good",
            uploader=self.user
        )
        self.collection.items.add(item)
        self.assertIn(item, self.collection.items.all())


class BorrowRequestTest(TestCase):
    def setUp(self):
        """Set up a user, an item, and a borrow request before each test."""
        self.user = User.objects.create_user(username="borrower", password="password")
        self.item = Item.objects.create(
            title="Borrowed Item",
            description="An item available for borrowing.",
            category="spices",
            condition="worn",
            uploader=self.user
        )
        self.borrow_request = BorrowRequest.objects.create(
            patron=self.user,
            item=self.item,
            status="pending"
        )

    def test_borrow_request_creation(self):
        """Test that a borrow request is created successfully."""
        self.assertEqual(self.borrow_request.patron, self.user)
        self.assertEqual(self.borrow_request.item, self.item)
        self.assertEqual(self.borrow_request.status, "pending")

    def test_approve_borrow_request(self):
        """Test approving a borrow request."""
        self.borrow_request.status = "approved"
        self.borrow_request.save()
        self.assertEqual(self.borrow_request.status, "approved")

    def test_deny_borrow_request(self):
        """Test denying a borrow request."""
        self.borrow_request.status = "denied"
        self.borrow_request.save()
        self.assertEqual(self.borrow_request.status, "denied")


class ItemVisibilityTest(TestCase):
    def setUp(self):
        """Set up users, collections, and items for testing visibility."""
        self.user = User.objects.create_user(username="testuser", password="password")
        self.item = Item.objects.create(
            title="Public Item",
            description="This item is not in a collection.",
            category="cookware",
            condition="good",
            uploader=self.user
        )
        self.private_collection = Collection.objects.create(
            title="Private Collection",
            description="This is a private collection.",
            created_by=self.user,
            is_private=True
        )
        self.private_collection.items.add(self.item)

    def test_item_in_private_collection_is_hidden(self):
        """Test that an item in a private collection is not visible."""
        hidden_items = Item.objects.filter(collections__is_private=True)
        self.assertIn(self.item, hidden_items)

