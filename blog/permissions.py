"""Object-level permissions for posts and comments."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Allow safe reads and allow object mutations only by its author."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and obj.author_id == request.user.pk


class IsPostAuthorOrReadOnly(IsOwnerOrReadOnly):
    """Allow post mutations only by the post author."""


class IsCommentAuthorOrReadOnly(IsOwnerOrReadOnly):
    """Allow comment mutations only by the comment author."""
