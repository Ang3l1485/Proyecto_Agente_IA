from typing import Any


def can_delete_business(user: Any, business: Any) -> bool:
    """Deletion rule without owner field: only staff/superusers may delete.

    - Unauthenticated users: cannot delete
    - Staff or superusers: can delete
    - Regular authenticated users: cannot delete
    """
    if not getattr(user, "is_authenticated", False):
        return False

    return bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
