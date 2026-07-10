from sqlalchemy.orm import Session

from . import models


def ordered_categories(db: Session):
    """Flat list of categories in depth-first order, parents before children."""
    all_categories = db.query(models.Category).order_by(models.Category.name).all()
    by_parent = {}
    for c in all_categories:
        by_parent.setdefault(c.parent_id, []).append(c)

    ordered = []

    def walk(parent_id):
        for c in by_parent.get(parent_id, []):
            ordered.append(c)
            walk(c.id)

    walk(None)
    return ordered


def build_category_tree(db: Session):
    """Nested category tree: [{id, name, children: [...]}, ...], roots first."""
    all_categories = db.query(models.Category).order_by(models.Category.name).all()
    by_parent = {}
    for c in all_categories:
        by_parent.setdefault(c.parent_id, []).append(c)

    def build(parent_id):
        return [
            {"id": c.id, "name": c.name, "children": build(c.id)}
            for c in by_parent.get(parent_id, [])
        ]

    return build(None)
