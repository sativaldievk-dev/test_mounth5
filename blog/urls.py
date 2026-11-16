"""Version 1 API URL patterns."""

from django.urls import path

from .views import (
    CommentDetailView,
    PostCommentListCreateView,
    PostDetailView,
    PostListCreateView,
)

app_name = "blog"

urlpatterns = [
    path("posts/", PostListCreateView.as_view(), name="post-list-create"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
    path(
        "posts/<int:post_pk>/comments/",
        PostCommentListCreateView.as_view(),
        name="post-comment-list-create",
    ),
    path("comments/<int:pk>/", CommentDetailView.as_view(), name="comment-detail"),
]
