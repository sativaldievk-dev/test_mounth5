"""Pagination used for the post collection."""

from rest_framework.pagination import PageNumberPagination


class PostPagination(PageNumberPagination):
    """Paginate posts with a configurable, bounded page size."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
