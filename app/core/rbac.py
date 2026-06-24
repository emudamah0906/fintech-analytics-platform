"""Role-Based Access Control (RBAC) — OWASP A01 (broken access control)."""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"        # full access, user management
    ANALYST = "analyst"    # read + write transactions
    VIEWER = "viewer"      # read-only analytics

    @classmethod
    def at_least(cls, role: Role) -> set[Role]:
        """Return the set of roles that satisfy a minimum privilege level."""
        order = [cls.VIEWER, cls.ANALYST, cls.ADMIN]
        idx = order.index(role)
        return set(order[idx:])
