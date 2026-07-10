import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base

STANDARD_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
GENDERS = ["Men", "Women", "Unisex"]
LOW_STOCK_THRESHOLD = 5

PO_STATUSES = ["draft", "ordered", "partial", "received", "cancelled"]
PRODUCT_STATUSES = ["active", "draft", "discontinued"]
ROLES = ["admin", "sales"]


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="sales")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    products = relationship("Product", back_populates="category")

    @property
    def full_name(self) -> str:
        return f"{self.parent.full_name} / {self.name}" if self.parent else self.name

    @property
    def depth(self) -> int:
        return self.parent.depth + 1 if self.parent else 0


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    style_code = Column(String, unique=True, nullable=False)
    gender = Column(String, nullable=False, default="Unisex")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    sell_price = Column(Float, nullable=False, default=0.0)
    description = Column(String, default="")
    material_composition = Column(String, default="")
    care_instructions = Column(String, default="")
    season = Column(String, default="")
    status = Column(String, nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    category = relationship("Category", back_populates="products")
    variants = relationship(
        "Variant", back_populates="product", cascade="all, delete-orphan"
    )
    supplier_links = relationship(
        "ProductSupplier", back_populates="product", cascade="all, delete-orphan"
    )
    attributes = relationship(
        "ProductAttribute", back_populates="product", cascade="all, delete-orphan"
    )
    images = relationship(
        "ProductImage", back_populates="product", cascade="all, delete-orphan"
    )

    @property
    def total_stock(self) -> int:
        return sum(v.quantity for v in self.variants)

    @property
    def is_low_stock(self) -> bool:
        return any(v.quantity <= LOW_STOCK_THRESHOLD for v in self.variants)

    @property
    def inventory_value(self) -> float:
        return sum(
            batch.quantity_remaining * batch.buy_price
            for v in self.variants
            for batch in v.batches
        )


class ProductAttribute(Base):
    __tablename__ = "product_attributes"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False, default="")

    product = relationship("Product", back_populates="attributes")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    color_name = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="images")


class Variant(Base):
    __tablename__ = "variants"
    __table_args__ = (
        UniqueConstraint("product_id", "size", "color_name", name="uq_product_size_color"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    size = Column(String, nullable=False)
    color_name = Column(String, nullable=False, default="")
    color_hex = Column(String, nullable=True)
    sku = Column(String, unique=True, nullable=False)
    barcode = Column(String, default="")
    quantity = Column(Integer, nullable=False, default=0)

    product = relationship("Product", back_populates="variants")
    movements = relationship(
        "StockMovement", back_populates="variant", cascade="all, delete-orphan"
    )
    batches = relationship(
        "StockBatch", back_populates="variant", cascade="all, delete-orphan",
        order_by="StockBatch.received_date",
    )

    @property
    def label(self) -> str:
        return f"{self.size} / {self.color_name}" if self.color_name else self.size

    @property
    def current_buy_price(self) -> float:
        if not self.batches:
            return 0.0
        return max(self.batches, key=lambda b: b.received_date).buy_price

    @property
    def average_batch_cost(self) -> float:
        on_hand = [b for b in self.batches if b.quantity_remaining > 0]
        total_qty = sum(b.quantity_remaining for b in on_hand)
        if not total_qty:
            return 0.0
        return sum(b.quantity_remaining * b.buy_price for b in on_hand) / total_qty


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    change = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    note = Column(String, default="")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    purchase_order_line_id = Column(
        Integer, ForeignKey("purchase_order_lines.id"), nullable=True
    )
    sale_item_id = Column(Integer, ForeignKey("sale_items.id"), nullable=True)

    variant = relationship("Variant", back_populates="movements")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    contact_name = Column(String, default="")
    phone = Column(String, default="")
    email = Column(String, default="")
    address = Column(String, default="")
    notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product_links = relationship(
        "ProductSupplier", back_populates="supplier", cascade="all, delete-orphan"
    )
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class ProductSupplier(Base):
    __tablename__ = "product_suppliers"
    __table_args__ = (
        UniqueConstraint("product_id", "supplier_id", name="uq_product_supplier"),
    )

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    cost_price = Column(Float, nullable=False, default=0.0)
    supplier_sku = Column(String, default="")

    product = relationship("Product", back_populates="supplier_links")
    supplier = relationship("Supplier", back_populates="product_links")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    status = Column(String, nullable=False, default="draft")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    ordered_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    notes = Column(String, default="")

    supplier = relationship("Supplier", back_populates="purchase_orders")
    lines = relationship(
        "PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan"
    )

    @property
    def total_cost(self) -> float:
        return sum(line.quantity_ordered * line.unit_cost for line in self.lines)

    @property
    def is_fully_received(self) -> bool:
        return all(line.quantity_received >= line.quantity_ordered for line in self.lines)


class PurchaseOrderLine(Base):
    __tablename__ = "purchase_order_lines"

    id = Column(Integer, primary_key=True, index=True)
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    quantity_ordered = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False, default=0.0)
    quantity_received = Column(Integer, nullable=False, default=0)

    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    variant = relationship("Variant")

    @property
    def quantity_remaining(self) -> int:
        return self.quantity_ordered - self.quantity_received


class StockBatch(Base):
    __tablename__ = "stock_batches"

    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    purchase_order_line_id = Column(
        Integer, ForeignKey("purchase_order_lines.id"), nullable=True
    )
    received_date = Column(DateTime, default=datetime.datetime.utcnow)
    quantity_received = Column(Integer, nullable=False)
    quantity_remaining = Column(Integer, nullable=False)
    buy_price = Column(Float, nullable=False, default=0.0)

    variant = relationship("Variant", back_populates="batches")
    purchase_order_line = relationship("PurchaseOrderLine")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    total = Column(Float, nullable=False, default=0.0)
    note = Column(String, default="")

    items = relationship(
        "SaleItem", back_populates="sale", cascade="all, delete-orphan"
    )

    @property
    def total_cost(self) -> float:
        return sum(item.quantity * item.unit_cost for item in self.items)

    @property
    def profit(self) -> float:
        return self.total - self.total_cost


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False, default=0.0)

    sale = relationship("Sale", back_populates="items")
    variant = relationship("Variant")

    @property
    def line_total(self) -> float:
        return self.quantity * self.unit_price
