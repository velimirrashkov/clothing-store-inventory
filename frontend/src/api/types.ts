/**
 * Hand-maintained to mirror the DRF serializers exactly. The spec's long-term intent is a
 * generated client from the OpenAPI schema at /api/schema/ (see architecture-spec.md §9) —
 * this is the pragmatic Phase 1 stand-in. Keep in sync with the backend api_serializers.py
 * files under each Django app.
 */

export interface User {
  public_id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
}

export interface Me {
  user: User;
  permissions: string[];
}

// --- catalog ------------------------------------------------------------------------------

export interface Category {
  id?: number;
  slug: string;
  name: string;
  parent: number | null;
  position: number;
  is_active?: boolean;
}

export interface ProductMedia {
  url: string;
  alt_text: string;
  position: number;
  is_primary: boolean;
}

export interface VariantStaff {
  id: number;
  public_id: string;
  sku: string;
  size: string;
  color: string;
  color_hex: string | null;
  price_amount: number;
  currency: string;
  compare_at_amount: number | null;
  in_stock: boolean;
  available: number;
  barcode: string | null;
  is_active: boolean;
}

export interface ProductAdminListItem {
  id: number;
  public_id: string;
  slug: string;
  name: string;
  brand: string;
  gender: string;
  status: "draft" | "active" | "archived";
  category: number;
}

export interface ProductAdminDetail extends ProductAdminListItem {
  description: string;
  season: string;
  variants: VariantStaff[];
  media: ProductMedia[];
}

export interface ProductWriteInput {
  name: string;
  slug?: string;
  description?: string;
  brand?: string;
  gender: "men" | "women" | "unisex" | "kids";
  season?: string;
  category: number;
}

export interface VariantMatrixInput {
  sizes: string[];
  colors: string[];
  base_price_amount: number;
  currency?: string;
}

export interface VariantUpdateInput {
  size?: string;
  color?: string;
  color_hex?: string | null;
  price_amount?: number;
  currency?: string;
  compare_at_amount?: number | null;
  barcode?: string | null;
  is_active?: boolean;
}

// --- inventory ----------------------------------------------------------------------------

export type StockMovementReason =
  | "receipt"
  | "sale_online"
  | "sale_pos"
  | "return"
  | "damage"
  | "loss"
  | "count_adjustment"
  | "correction"
  | "initial_load";

export interface StockLevel {
  variant: number;
  sku: string;
  location: number;
  on_hand: number;
  reserved: number;
  available: number;
  updated_at: string;
}

export interface StockMovement {
  id: number;
  variant: number;
  location: number;
  delta: number;
  reason: StockMovementReason;
  reference: string | null;
  note: string | null;
  actor: number | null;
  created_at: string;
}

export interface MovementCreateInput {
  variant_id: number;
  delta: number;
  reason: StockMovementReason;
  note?: string;
  reference?: string;
}

export interface StockCount {
  id: number;
  location: number;
  status: "open" | "closed";
  started_by: number;
  started_at: string;
  closed_at: string | null;
}

export interface StockCountLine {
  id: number;
  count: number;
  variant: number;
  sku: string;
  expected: number;
  counted: number | null;
  counted_by: number | null;
  counted_at: string | null;
}

// --- orders -------------------------------------------------------------------------------

export interface OrderLine {
  sku: string;
  product_name: string;
  size: string;
  color: string;
  quantity: number;
  unit_amount: number;
  line_total: number;
}

export interface Order {
  public_id: string;
  reference: string;
  channel: "online" | "pos";
  status: string;
  payment_status: "pending" | "paid" | "refunded" | "failed";
  payment_method: "cash" | "card" | null;
  subtotal_amount: number;
  discount_amount: number;
  shipping_amount: number;
  tax_amount: number;
  total_amount: number;
  currency: string;
  placed_at: string;
  lines: OrderLine[];
}

export interface PosOrderLineInput {
  variant_id: number;
  quantity: number;
}

export interface PosOrderCreateInput {
  lines: PosOrderLineInput[];
  payment_method: "cash" | "card";
}

export interface Paginated<T> {
  next: string | null;
  previous: string | null;
  results: T[];
}
