from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Docstring for StandardPagination
    """
    page_size = 20
    page_size_query_param = page_size
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "data": data,
            "meta": {
                "page":         self.page.number,
                "page_size":    self.get_page_size(self.request),
                "total":        self.page.paginator.count,
                "total_pages":  self.page.paginator.num_pages,
                "has_next":     self.page.has_next(),
                "has_previous": self.page.has_previous(),
            }
        })
    
    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "data":    schema,
                "meta": {
                    "type": "object",
                    "properties": {
                        "page":         {"type": "integer"},
                        "page_size":    {"type": "integer"},
                        "total":        {"type": "integer"},
                        "total_pages":  {"type": "integer"},
                        "has_next":     {"type": "boolean"},
                        "has_previous": {"type": "boolean"},
                    }
                }
            }
        }
    

class LargePagination(StandardPagination):
    """برای لیست‌های ادمین"""
    page_size     = 50
    max_page_size = 500