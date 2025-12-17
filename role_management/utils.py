def has_permission(permissions: int, action) -> bool:
    return (permissions & action) != 0