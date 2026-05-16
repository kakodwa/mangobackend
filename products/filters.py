from rest_framework.filters import BaseFilterBackend

class DistrictFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        district = request.query_params.get('district')
        if district:
            return queryset.filter(shop__district__iexact=district)
        return queryset