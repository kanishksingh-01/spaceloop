def paginate(query_set, page=1, per_page=10):
    return query_set.paginate(page=page, per_page=per_page, error_out=False)
