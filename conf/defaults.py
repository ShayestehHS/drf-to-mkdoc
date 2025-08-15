DEFAULTS = {
    "TEMPLATES_DIR": None,  # Optional override directory
    "PAGINATION_MAP": {
        "rest_framework.pagination.PageNumberPagination": "pagination/page_number.md",
        "rest_framework.pagination.LimitOffsetPagination": "pagination/limit_offset.md",
        "rest_framework.pagination.CursorPagination": "pagination/cursor.md",
    },
    "INDEX_TEMPLATE": "index.md",
    "AUTH_TEMPLATE": "auth.md",
    "PATH_PARAM_SUBSTITUTOR": None,
}
