from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination


class CollectionPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'size'
    max_page_size = 100

    def get_page_size(self, request):
        value = request.query_params.get(self.page_size_query_param)
        if value is None:
            return self.page_size
        try:
            size = int(value)
        except (TypeError, ValueError):
            raise ValidationError({'size': ['Enter a positive integer.']})
        if size <= 0:
            raise ValidationError({'size': ['Enter a positive integer.']})
        return min(size, self.max_page_size)
