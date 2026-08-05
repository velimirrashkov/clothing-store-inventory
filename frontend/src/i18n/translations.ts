/**
 * Bulgarian + English UI strings, BG default (this is a Bulgarian-market business — see the
 * i18n decision this repo made on the previous stack, same rationale here).
 *
 * Only static UI chrome lives here — labels, buttons, messages. Business data the user types
 * in (product names, supplier names, notes) is never translated. Internal status/reason codes
 * stored in the database stay as fixed English strings (e.g. "correction", "active") — only
 * their on-screen label is looked up here via reason.* / status.* / gender.* keys, so filtering
 * and API payloads never have to deal with language.
 *
 * Keep this file in sync going forward: every new user-facing string in the back office needs
 * an entry here and a t() call at its call site, in both languages.
 */

export type Locale = "bg" | "en";

type Entry = Record<Locale, string>;

export const translations: Record<string, Entry> = {
  // --- common -------------------------------------------------------------------------------
  "common.loading": { bg: "Зареждане…", en: "Loading…" },
  "common.save": { bg: "Запази", en: "Save" },
  "common.saving": { bg: "Запазване…", en: "Saving…" },
  "common.save_changes": { bg: "Запази промените", en: "Save changes" },
  "common.cancel": { bg: "Отказ", en: "Cancel" },
  "common.create": { bg: "Създай", en: "Create" },
  "common.edit": { bg: "Редактирай", en: "Edit" },
  "common.close": { bg: "Затвори", en: "Close" },
  "common.choose": { bg: "Изберете…", en: "Choose…" },
  "common.name": { bg: "Име", en: "Name" },
  "common.email": { bg: "Имейл", en: "Email" },
  "common.phone": { bg: "Телефон", en: "Phone" },

  // --- nav ----------------------------------------------------------------------------------
  "nav.brand": { bg: "Магазин за облекло", en: "Clothing Store" },
  "nav.products": { bg: "Продукти", en: "Products" },
  "nav.inventory": { bg: "Наличности", en: "Inventory" },
  "nav.stocktake": { bg: "Инвентаризация", en: "Stocktake" },
  "nav.deliveries": { bg: "Доставки", en: "Deliveries" },
  "nav.suppliers": { bg: "Доставчици", en: "Suppliers" },
  "nav.sell": { bg: "Продажба", en: "Sell" },
  "nav.sign_out": { bg: "Изход", en: "Sign out" },
  "nav.no_permission": { bg: "Нямате права за преглед на тази страница.", en: "You don't have permission to view this page." },

  // --- auth -----------------------------------------------------------------------------------
  "auth.sign_in_title": { bg: "Вход в бек офиса", en: "Back office sign in" },
  "auth.email": { bg: "Имейл", en: "Email" },
  "auth.password": { bg: "Парола", en: "Password" },
  "auth.sign_in": { bg: "Вход", en: "Sign in" },
  "auth.signing_in": { bg: "Влизане…", en: "Signing in…" },
  "auth.generic_error": { bg: "Възникна грешка.", en: "Something went wrong." },

  // --- products -------------------------------------------------------------------------------
  "products.title": { bg: "Продукти", en: "Products" },
  "products.add_category": { bg: "+ Категория", en: "+ Category" },
  "products.add_product": { bg: "+ Продукт", en: "+ Product" },
  "products.select_prompt": { bg: "Изберете продукт от дървото или създайте нов.", en: "Select a product from the tree, or create a new one." },
  "products.no_categories": { bg: "Все още няма категории — създайте, за да започнете.", en: "No categories yet — create one to get started." },
  "products.empty": { bg: "Празно", en: "Empty" },
  "products.category_name_placeholder": { bg: "Име на категория", en: "Category name" },
  "products.no_parent": { bg: "Без родител (най-горно ниво)", en: "No parent (top level)" },
  "products.product_name_placeholder": { bg: "Име на продукт", en: "Product name" },
  "products.choose_category": { bg: "Изберете категория…", en: "Choose category…" },
  "products.error_choose_category": { bg: "Изберете категория.", en: "Choose a category." },
  "products.error_create_category": { bg: "Категорията не можа да бъде създадена.", en: "Could not create category." },
  "products.error_create_product": { bg: "Продуктът не можа да бъде създаден.", en: "Could not create product." },
  "products.archive": { bg: "Архивирай", en: "Archive" },
  "products.brand": { bg: "Марка", en: "Brand" },
  "products.season": { bg: "Сезон", en: "Season" },
  "products.description": { bg: "Описание", en: "Description" },
  "products.variants": { bg: "Варианти", en: "Variants" },
  "products.assign_missing_barcodes": { bg: "Присвои липсващи баркодове", en: "Assign missing barcodes" },
  "products.generate_variants": { bg: "Генерирай варианти", en: "Generate variants" },
  "products.sizes_csv": { bg: "Размери (разделени със запетая)", en: "Sizes (comma-separated)" },
  "products.colors_csv": { bg: "Цветове (разделени със запетая)", en: "Colours (comma-separated)" },
  "products.base_price": { bg: "Базова цена", en: "Base price" },
  "products.error_invalid_price": { bg: "Въведете валидна цена.", en: "Enter a valid price." },
  "products.error_generate_variants": { bg: "Вариантите не можаха да бъдат генерирани.", en: "Could not generate variants." },
  "products.generate_grid": { bg: "Генерирай матрица", en: "Generate grid" },
  "products.generating": { bg: "Генериране…", en: "Generating…" },
  "products.col_sku": { bg: "SKU", en: "SKU" },
  "products.col_size": { bg: "Размер", en: "Size" },
  "products.col_color": { bg: "Цвят", en: "Colour" },
  "products.col_price": { bg: "Цена", en: "Price" },
  "products.col_available": { bg: "Наличност", en: "Available" },
  "products.col_barcode": { bg: "Баркод", en: "Barcode" },
  "products.adjust": { bg: "Коригирай", en: "Adjust" },
  "products.quantity_change": { bg: "Промяна в количеството", en: "Quantity change" },
  "products.quantity_placeholder": { bg: "напр. 10 или -2", en: "e.g. 10 or -2" },
  "products.reason": { bg: "Причина", en: "Reason" },
  "products.error_quantity": { bg: "Въведете ненулево цяло число.", en: "Enter a non-zero whole number." },
  "products.error_adjust": { bg: "Наличността не можа да бъде коригирана.", en: "Could not adjust stock." },
  "products.no_variants": { bg: "Все още няма варианти — генерирайте матрица размер/цвят по-горе.", en: "No variants yet — generate a size/colour grid above." },
  "products.vendor_catalog": { bg: "Каталог на доставчици", en: "Vendor catalog" },
  "products.vendor_catalog_hint": { bg: "Обявени цени от доставчици, които предлагат този продукт — само за мениджъри, тъй като това са данни за маржа.", en: "Quoted costs from suppliers who carry this product — manager-only, since this is margin data." },
  "products.supplier": { bg: "Доставчик", en: "Supplier" },
  "products.cost": { bg: "Цена", en: "Cost" },
  "products.save_cost": { bg: "Запази цена", en: "Save cost" },
  "products.error_vendor_cost": { bg: "Изберете доставчик и въведете валидна цена.", en: "Choose a supplier and enter a valid cost." },
  "products.error_save_cost": { bg: "Цената не можа да бъде запазена.", en: "Could not save cost." },

  // --- reason (stock movement) -----------------------------------------------------------------
  "reason.correction": { bg: "Корекция (преброяване)", en: "Correction (recount)" },
  "reason.damage": { bg: "Повреда", en: "Damage" },
  "reason.loss": { bg: "Загуба / кражба", en: "Loss / theft" },
  "reason.initial_load": { bg: "Първоначално зареждане", en: "Initial load" },

  // --- gender ---------------------------------------------------------------------------------
  "gender.unisex": { bg: "унисекс", en: "unisex" },
  "gender.men": { bg: "мъже", en: "men" },
  "gender.women": { bg: "жени", en: "women" },
  "gender.kids": { bg: "деца", en: "kids" },

  // --- status ---------------------------------------------------------------------------------
  "status.draft": { bg: "чернова", en: "draft" },
  "status.active": { bg: "активен", en: "active" },
  "status.archived": { bg: "архивиран", en: "archived" },

  // --- inventory ------------------------------------------------------------------------------
  "inventory.barcode_lookup": { bg: "Търсене по баркод", en: "Barcode lookup" },
  "inventory.search_results": { bg: "Резултати от търсенето", en: "Search results" },
  "inventory.low_stock": { bg: "Ниска наличност", en: "Low stock" },
  "inventory.search_by_sku": { bg: "Търсене по SKU", en: "Search by SKU" },
  "inventory.low_stock_only": { bg: "Само ниска наличност (≤5)", en: "Low stock only (≤5)" },
  "inventory.nothing_to_show": { bg: "Няма какво да се покаже.", en: "Nothing to show." },
  "inventory.col_on_hand": { bg: "В наличност", en: "On hand" },
  "inventory.col_reserved": { bg: "Резервирано", en: "Reserved" },
  "inventory.scan_or_type": { bg: "Сканирайте или въведете баркод", en: "Scan or type a barcode" },
  "inventory.look_up": { bg: "Търси", en: "Look up" },
  "inventory.use_camera": { bg: "Използвай камера", en: "Use camera" },
  "inventory.stop_camera": { bg: "Спри камерата", en: "Stop camera" },
  "inventory.not_found": { bg: "Няма вариант с този баркод.", en: "No variant with that barcode." },
  "inventory.available": { bg: "Наличност", en: "Available" },

  // --- stocktake ------------------------------------------------------------------------------
  "stocktake.title": { bg: "Инвентаризации", en: "Stocktakes" },
  "stocktake.open_new": { bg: "Отвори нова", en: "Open new" },
  "stocktake.open": { bg: "Отворени", en: "Open" },
  "stocktake.closed": { bg: "Затворени", en: "Closed" },
  "stocktake.none_open": { bg: "Няма отворени", en: "None open" },
  "stocktake.count_number": { bg: "Преброяване №", en: "Count #" },
  "stocktake.select_prompt": { bg: "Отворете нова инвентаризация или изберете от списъка.", en: "Open a new stocktake or select one from the list." },
  "stocktake.lines": { bg: "реда", en: "lines" },
  "stocktake.not_yet_counted": { bg: "все още непреброени", en: "not yet counted" },
  "stocktake.submit_all": { bg: "Изпрати всички", en: "Submit all" },
  "stocktake.submitting": { bg: "Изпращане…", en: "Submitting…" },
  "stocktake.close_count": { bg: "Затвори инвентаризацията", en: "Close count" },
  "stocktake.reopen": { bg: "Отвори отново за корекция", en: "Reopen for correction" },
  "stocktake.reopening": { bg: "Отваряне отново…", en: "Reopening…" },
  "stocktake.reopen_title": { bg: "Обръща корекциите по наличността на тази инвентаризация с компенсиращ запис и я отваря отново за корекция — нищо в историята не се изтрива.", en: "Reverses this count's stock adjustments with a compensating entry, then reopens it for correction — nothing in the history is deleted." },
  "stocktake.col_expected": { bg: "Очаквано", en: "Expected" },
  "stocktake.col_counted": { bg: "Преброено", en: "Counted" },
  "stocktake.submit": { bg: "Изпрати", en: "Submit" },
  "stocktake.discrepancy": { bg: "разлика", en: "discrepancy" },
  "stocktake.error_whole_number": { bg: "Въведете цяло число ≥ 0.", en: "Enter a whole number ≥ 0." },
  "stocktake.error_submit": { bg: "Промените не можаха да бъдат изпратени.", en: "Could not submit changes." },
  "stocktake.error_submit_line": { bg: "Не можа да бъде изпратено.", en: "Could not submit." },

  // --- sell -----------------------------------------------------------------------------------
  "sell.browse": { bg: "Разглеждане", en: "Browse" },
  "sell.pick_product": { bg: "Изберете продукт, за да видите вариантите му.", en: "Pick a product to see its variants." },
  "sell.cart": { bg: "Кошница", en: "Cart" },
  "sell.cart_empty": { bg: "Кошницата е празна.", en: "Cart is empty." },
  "sell.total": { bg: "Общо", en: "Total" },
  "sell.cash": { bg: "в брой", en: "cash" },
  "sell.card": { bg: "карта", en: "card" },
  "sell.complete_sale": { bg: "Завърши продажбата", en: "Complete sale" },
  "sell.completing": { bg: "Завършване…", en: "Completing…" },
  "sell.error_complete": { bg: "Продажбата не можа да бъде завършена.", en: "Could not complete sale." },
  "sell.in_stock": { bg: "в наличност", en: "in stock" },
  "sell.no_variants": { bg: "Няма варианти за този продукт.", en: "No variants for this product." },
  "sell.sale_complete": { bg: "Продажбата е завършена", en: "Sale complete" },
  "sell.new_sale": { bg: "Нова продажба", en: "New sale" },

  // --- suppliers ------------------------------------------------------------------------------
  "suppliers.title": { bg: "Доставчици", en: "Suppliers" },
  "suppliers.add": { bg: "+ Доставчик", en: "+ Supplier" },
  "suppliers.none_yet": { bg: "Все още няма доставчици.", en: "No suppliers yet." },
  "suppliers.col_contact": { bg: "За контакт", en: "Contact" },
  "suppliers.name_placeholder": { bg: "Име", en: "Name" },
  "suppliers.email_placeholder": { bg: "Имейл", en: "Email" },
  "suppliers.phone_placeholder": { bg: "Телефон", en: "Phone" },
  "suppliers.error_create": { bg: "Доставчикът не можа да бъде създаден.", en: "Could not create supplier." },

  // --- deliveries -----------------------------------------------------------------------------
  "deliveries.browse_products": { bg: "Разглеждане на продукти", en: "Browse products" },
  "deliveries.delivery_number": { bg: "Доставка №", en: "Delivery #" },
  "deliveries.received": { bg: "получена — наличността е обновена.", en: "received — stock updated." },
  "deliveries.receive_another": { bg: "Приеми друга", en: "Receive another" },
  "deliveries.pick_product": { bg: "Изберете продукт вляво, за да добавите редове към тази доставка.", en: "Pick a product on the left to add lines to this delivery." },
  "deliveries.new_delivery": { bg: "Нова доставка", en: "New delivery" },
  "deliveries.choose_supplier": { bg: "Изберете доставчик…", en: "Choose supplier…" },
  "deliveries.reference_placeholder": { bg: "Номер на фактура / стокова разписка (незадължително)", en: "Invoice / delivery note ref (optional)" },
  "deliveries.no_lines": { bg: "Все още няма редове.", en: "No lines yet." },
  "deliveries.qty": { bg: "Кол.", en: "Qty" },
  "deliveries.unit_cost": { bg: "Ед. цена", en: "Unit cost" },
  "deliveries.receive": { bg: "Приеми доставка", en: "Receive delivery" },
  "deliveries.receiving": { bg: "Приемане…", en: "Receiving…" },
  "deliveries.error_choose_supplier": { bg: "Изберете доставчик.", en: "Choose a supplier." },
  "deliveries.error_receive": { bg: "Доставката не можа да бъде приета.", en: "Could not receive delivery." },
  "deliveries.currently_in_stock": { bg: "в момента в наличност", en: "currently in stock" },
  "deliveries.recent": { bg: "Скорошни доставки", en: "Recent deliveries" },
  "deliveries.col_supplier": { bg: "Доставчик", en: "Supplier" },
  "deliveries.col_reference": { bg: "Референция", en: "Reference" },
  "deliveries.col_lines": { bg: "Редове", en: "Lines" },
  "deliveries.col_date": { bg: "Дата", en: "Date" },
};
