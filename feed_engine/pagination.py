from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class UnifiedSearchPagination(PageNumberPagination):
    page_size = 15  # Number of items per scroll fetch
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': len(data), # Combined count for current page context
            'results': data
        })