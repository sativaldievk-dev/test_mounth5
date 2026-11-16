"""Serializers for the blog API."""

from rest_framework import serializers

from .models import Comment, Post


class PostSerializer(serializers.ModelSerializer):
    """Serialize post content while keeping ownership server-controlled."""

    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "title",
            "body",
            "created_at",
            "updated_at",
            "is_published",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")


class CommentSerializer(serializers.ModelSerializer):
    """Serialize comments without accepting ownership or moderation fields."""

    post = serializers.PrimaryKeyRelatedField(read_only=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "author",
            "body",
            "created_at",
            "updated_at",
            "is_approved",
        )
        read_only_fields = (
            "id",
            "post",
            "author",
            "created_at",
            "updated_at",
            "is_approved",
        )
