class BaseFeedService:
    PAGE_SIZE = 20
    HORIZONTAL_LIMIT = 10

    def format_item(self, item_type, obj):
        return {
            "type": item_type,
            "data": obj
        }

    def paginate(self, queryset, last_id):
        if last_id:
            queryset = queryset.filter(id__lt=last_id)
        return queryset.order_by("-id")[:self.PAGE_SIZE]