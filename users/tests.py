from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from users.models import UserProfile

class UserRoleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

    def test_assign_patron_role(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("patron_login"), follow=True)
        self.user.refresh_from_db()
        self.assertTrue(self.user.groups.filter(name="Patron").exists())
        self.assertEqual(self.client.session.get("current_role"), "Patron")
        self.assertEqual(response.status_code, 200)

    def test_assign_librarian_role(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("librarian_login"), follow=True)
        self.user.refresh_from_db()
        self.assertTrue(self.user.groups.filter(name="Librarian").exists())
        self.assertEqual(self.client.session.get("current_role"), "Librarian")
        self.assertEqual(response.status_code, 200)

    def test_role_conflict_patron_to_librarian(self):
        patron_group = Group.objects.get_or_create(name="Patron")[0]
        self.user.groups.add(patron_group)
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("librarian_login"))
        self.assertFalse(self.user.groups.filter(name="Librarian").exists())
        self.assertIn("/?error=role_conflict_patron", response.url)

    def test_role_conflict_librarian_to_patron(self):
        librarian_group = Group.objects.get_or_create(name="Librarian")[0]
        self.user.groups.add(librarian_group)
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("patron_login"))
        self.assertFalse(self.user.groups.filter(name="Patron").exists())
        self.assertIn("/?error=role_conflict_librarian", response.url)

class ProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

    def test_authenticated_profile_view(self):
        self.client.login(username="testuser", password="testpassword")
        response = self.client.get(reverse("profile_info"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/profile_info.html")
        self.assertContains(response, "testuser")

    def test_unauthenticated_profile_view(self):
        response = self.client.get(reverse("profile_info"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_upload_valid_profile_photo(self):
        self.client.login(username="testuser", password="testpassword")
        image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        response = self.client.post(reverse("upload_profile_photo"), {"profile_picture": image}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.profile.profile_picture)
