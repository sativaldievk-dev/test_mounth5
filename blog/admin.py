"""Admin configuration for moderation and content management."""

from django.contrib import admin

from .models import Comment, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Admin list and filters for posts."""

    list_display = ("title", "author", "is_published", "created_at", "updated_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "body", "author__username")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin moderation interface for comments."""

    list_display = ("post", "author", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("body", "post__title", "author__username")
    readonly_fields = ("created_at", "updated_at")
    actions = ("approve_comments",)

    @admin.action(description="Одобрить выбранные комментарии")
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
