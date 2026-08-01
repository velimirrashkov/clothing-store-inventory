"""
Role -> permission grants, from architecture-spec.md §4.2 / §6.3.
Applied by the `seed_roles` management command (apps/accounts/management/commands/seed_roles.py),
which creates these as Django Groups. Roles are just permission bundles: code must always check
`user.has_perm(...)`, never `user.groups.filter(name=...)`.
"""

ROLE_PERMISSIONS = {
    "worker": [
        "catalog.view_product",
        "catalog.view_variant",
        "catalog.view_category",
        "inventory.adjust_stock",
        "inventory.run_count",
        "orders.fulfil_order",
        "orders.create_pos_order",
    ],
    "manager": [
        "pricing.change_discount",
        "catalog.change_product",
        "catalog.add_product",
        "orders.refund_order",
        "orders.view_reports",  # co-located on orders.Order (see apps/orders/models.py Meta.permissions)
    ],
    "admin": [
        "accounts.manage_users",
        "accounts.assign_roles",
    ],
}

# Cumulative: manager inherits worker, admin inherits manager (see architecture-spec.md §6.3 role matrix).
ROLE_INHERITANCE = {
    "worker": [],
    "manager": ["worker"],
    "admin": ["manager"],
}
