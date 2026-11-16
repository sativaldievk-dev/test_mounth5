"""Automated API tests for posts, comments, permissions, and JWT."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Comment, Post

User = get_user_model()


class BlogAPITestCase(APITestCase):
    """Shared users and helpers for API tests."""

    def setUp(self):
        self.author = User.objects.create_user(
            username="author", password="author-password-123"
        )
        self.other_user = User.objects.create_user(
            username="other", password="other-password-123"
        )
        self.post = Post.objects.create(
            author=self.author,
            title="Published post",
            body="Post body",
            is_published=True,
        )

    def authenticate_as(self, user):
        """Authenticate the test client as the selected user."""
        self.client.force_authenticate(user=user)

    def post_url(self, post=None):
        """Return the detail URL for a post."""
        return reverse("blog:post-detail", args=[post.pk if post else self.post.pk])

    def comments_url(self, post=None):
        """Return the nested comments URL for a post."""
        return reverse(
            "blog:post-comment-list-create",
            args=[post.pk if post else self.post.pk],
        )


class PostAPITests(BlogAPITestCase):
    """Tests for post CRUD, visibility, ownership, and pagination."""

    def test_authenticated_user_creates_post_as_self(self):
        self.authenticate_as(self.author)
        response = self.client.post(
            reverse("blog:post-list-create"),
            {
                "author": self.other_user.pk,
                "title": "A new post",
                "body": "A useful post body",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_post = Post.objects.get(pk=response.data["id"])
        self.assertEqual(created_post.author, self.author)
        self.assertFalse(created_post.is_published)
        self.assertIsNotNone(created_post.created_at)
        self.assertIsNotNone(created_post.updated_at)

    def test_guest_cannot_create_post(self):
        response = self.client.post(
            reverse("blog:post-list-create"),
            {"title": "Guest post", "body": "Body"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_guests_list_only_published_posts_with_pagination(self):
        for number in range(11):
            Post.objects.create(
                author=self.author,
                title=f"Published {number}",
                body="Body",
                is_published=True,
            )
        Post.objects.create(author=self.author, title="Draft", body="Body")

        response = self.client.get(reverse("blog:post-list-create"), {"page_size": 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(len(response.data["results"]), 5)
        self.assertIsNotNone(response.data["next"])
        self.assertFalse(
            any(item["title"] == "Draft" for item in response.data["results"])
        )

    def test_authenticated_author_can_see_own_unpublished_post(self):
        draft = Post.objects.create(author=self.author, title="Draft", body="Body")
        self.authenticate_as(self.author)

        list_response = self.client.get(reverse("blog:post-list-create"))
        detail_response = self.client.get(self.post_url(draft))

        self.assertIn(draft.pk, [item["id"] for item in list_response.data["results"]])
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)

    def test_guest_cannot_retrieve_unpublished_post(self):
        draft = Post.objects.create(author=self.author, title="Draft", body="Body")

        response = self.client.get(self.post_url(draft))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_retrieve_another_users_unpublished_post(self):
        draft = Post.objects.create(author=self.author, title="Draft", body="Body")
        self.authenticate_as(self.other_user)

        response = self.client.get(self.post_url(draft))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_guest_can_retrieve_published_post_detail(self):
        response = self.client.get(self.post_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.post.pk)
        self.assertEqual(response.data["title"], self.post.title)

    def test_author_can_put_patch_and_delete_own_post(self):
        self.authenticate_as(self.author)
        put_response = self.client.put(
            self.post_url(),
            {
                "author": self.other_user.pk,
                "title": "Replaced title",
                "body": "Replaced body",
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.author, self.author)
        self.assertEqual(self.post.title, "Replaced title")

        patch_response = self.client.patch(
            self.post_url(), {"title": "Patched title"}, format="json"
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Patched title")

        delete_response = self.client.delete(self.post_url())
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_user_cannot_update_or_delete_another_users_post(self):
        self.authenticate_as(self.other_user)

        update_response = self.client.patch(
            self.post_url(), {"title": "Hijacked"}, format="json"
        )
        delete_response = self.client.delete(self.post_url())

        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "Published post")

    def test_invalid_post_data_returns_validation_errors(self):
        self.authenticate_as(self.author)

        missing_title = self.client.post(
            reverse("blog:post-list-create"), {"body": "Body"}, format="json"
        )
        blank_title = self.client.post(
            reverse("blog:post-list-create"),
            {"title": "   ", "body": "Body"},
            format="json",
        )

        self.assertEqual(missing_title.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", missing_title.data)
        self.assertEqual(blank_title.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", blank_title.data)


class CommentAPITests(BlogAPITestCase):
    """Tests for comment creation, moderation visibility, and ownership."""

    def test_authenticated_user_creates_unapproved_comment_as_self(self):
        self.authenticate_as(self.other_user)
        response = self.client.post(
            self.comments_url(),
            {
                "post": self.post.pk + 100,
                "author": self.author.pk,
                "body": "A comment",
                "is_approved": True,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment = Comment.objects.get(pk=response.data["id"])
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.other_user)
        self.assertFalse(comment.is_approved)
        self.assertIsNotNone(comment.created_at)
        self.assertIsNotNone(comment.updated_at)

    def test_guest_cannot_create_comment(self):
        response = self.client.post(
            self.comments_url(), {"body": "Guest comment"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_comments_list_shows_approved_and_authors_own_pending_comments(self):
        approved = Comment.objects.create(
            post=self.post,
            author=self.author,
            body="Approved",
            is_approved=True,
        )
        pending_by_other = Comment.objects.create(
            post=self.post,
            author=self.other_user,
            body="Pending by other",
        )

        guest_response = self.client.get(self.comments_url())
        self.assertEqual(guest_response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in guest_response.data], [approved.pk])

        self.authenticate_as(self.other_user)
        owner_response = self.client.get(self.comments_url())
        self.assertEqual(
            {item["id"] for item in owner_response.data},
            {approved.pk, pending_by_other.pk},
        )

    def test_pending_comment_is_hidden_from_other_users(self):
        pending = Comment.objects.create(
            post=self.post,
            author=self.author,
            body="Pending",
        )
        self.authenticate_as(self.other_user)

        response = self.client.get(reverse("blog:comment-detail", args=[pending.pk]))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_on_unpublished_post_is_hidden_from_guests(self):
        draft = Post.objects.create(author=self.author, title="Draft", body="Body")
        approved_comment = Comment.objects.create(
            post=draft,
            author=self.author,
            body="Approved on a draft",
            is_approved=True,
        )

        response = self.client.get(
            reverse("blog:comment-detail", args=[approved_comment.pk])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_author_can_update_and_delete_own_comment(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.other_user,
            body="Original",
        )
        self.authenticate_as(self.other_user)

        update_response = self.client.patch(
            reverse("blog:comment-detail", args=[comment.pk]),
            {"author": self.author.pk, "body": "Updated"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.author, self.other_user)
        self.assertEqual(comment.body, "Updated")

        delete_response = self.client.delete(
            reverse("blog:comment-detail", args=[comment.pk])
        )
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_user_cannot_update_or_delete_another_users_comment(self):
        comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            body="Approved comment",
            is_approved=True,
        )
        self.authenticate_as(self.other_user)

        update_response = self.client.patch(
            reverse("blog:comment-detail", args=[comment.pk]),
            {"body": "Hijacked"},
            format="json",
        )
        delete_response = self.client.delete(
            reverse("blog:comment-detail", args=[comment.pk])
        )

        self.assertEqual(update_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)

    def test_invalid_comment_body_returns_validation_error(self):
        self.authenticate_as(self.author)

        response = self.client.post(
            self.comments_url(), {"body": "   "}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("body", response.data)

    def test_comments_cannot_be_added_to_unpublished_posts(self):
        draft = Post.objects.create(author=self.author, title="Draft", body="Body")
        self.authenticate_as(self.other_user)

        response = self.client.post(
            self.comments_url(draft), {"body": "A comment"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class JWTAuthenticationTests(BlogAPITestCase):
    """Tests for obtaining and refreshing JWT access tokens."""

    def test_token_obtain_and_refresh(self):
        obtain_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "author", "password": "author-password-123"},
            format="json",
        )

        self.assertEqual(obtain_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", obtain_response.data)
        self.assertIn("refresh", obtain_response.data)

        refresh_response = self.client.post(
            reverse("token_refresh"),
            {"refresh": obtain_response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

    def test_jwt_token_authorizes_post_creation(self):
        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "author", "password": "author-password-123"},
            format="json",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}"
        )

        response = self.client.post(
            reverse("blog:post-list-create"),
            {"title": "JWT post", "body": "Created with a token"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.get(pk=response.data["id"]).author, self.author)
