"""API views for posts and comments."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Comment, Post
from .pagination import PostPagination
from .permissions import IsCommentAuthorOrReadOnly, IsPostAuthorOrReadOnly
from .serializers import CommentSerializer, PostSerializer


def visible_posts_for(user):
    """Return published posts and, for a signed-in author, their drafts."""
    posts = Post.objects.all()
    if user.is_authenticated:
        return posts.filter(Q(is_published=True) | Q(author=user)).distinct()
    return posts.filter(is_published=True)


def visible_comments_for(comments, user):
    """Filter comments by post visibility, approval, and comment ownership."""
    if user.is_staff:
        return comments

    visible_posts = Q(post__is_published=True)
    if user.is_authenticated:
        visible_posts |= Q(post__author=user)
        visible_comments = Q(is_approved=True) | Q(author=user)
    else:
        visible_comments = Q(is_approved=True)
    return comments.filter(visible_posts, visible_comments).distinct()


class PostListCreateView(generics.ListCreateAPIView):
    """List visible posts or create a post for the authenticated user."""

    serializer_class = PostSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = PostPagination

    def get_queryset(self):
        return visible_posts_for(self.request.user).select_related("author")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Read a visible post or let its author update and delete it."""

    serializer_class = PostSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsPostAuthorOrReadOnly)

    def get_queryset(self):
        return visible_posts_for(self.request.user).select_related("author")


class PostCommentListCreateView(generics.ListCreateAPIView):
    """List visible comments for a post or add a comment to a published post."""

    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_post(self):
        if not hasattr(self, "_post"):
            posts = visible_posts_for(self.request.user)
            self._post = get_object_or_404(posts, pk=self.kwargs["post_pk"])
        return self._post

    def get_queryset(self):
        post = self.get_post()
        comments = Comment.objects.filter(post=post).select_related("author", "post")
        return visible_comments_for(comments, self.request.user)

    def perform_create(self, serializer):
        post = self.get_post()
        if not post.is_published:
            raise ValidationError("Comments can only be added to published posts.")
        serializer.save(post=post, author=self.request.user)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Read visible comments or let their authors update and delete them."""

    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsCommentAuthorOrReadOnly)

    def get_queryset(self):
        comments = Comment.objects.select_related("author", "post")
        return visible_comments_for(comments, self.request.user)
