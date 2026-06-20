from rest_framework.views import APIView
from rest_framework.response import Response

from .cj_services import CJService


class ProductListView(APIView):

    def get(self, request):

        page = request.GET.get("page", 1)

        cj = CJService()

        products = cj.get_products(page=page)

        return Response(products)


class ProductDetailView(APIView):

    def get(self, request, pid):

        cj = CJService()

        product = cj.product_detail(pid)

        return Response(product)