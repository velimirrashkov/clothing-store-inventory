from fastapi import Request

DEFAULT_LANG = "bg"
SUPPORTED_LANGS = ["bg", "en"]
LANG_COOKIE = "lang"

TRANSLATIONS = {
    "brand.name": {"bg": "Магазин за дрехи", "en": "Clothing Store"},

    "nav.inventory": {"bg": "Инвентар", "en": "Inventory"},
    "nav.sell": {"bg": "Продажба", "en": "Sell"},
    "nav.purchase_orders": {"bg": "Поръчки за доставка", "en": "Purchase Orders"},
    "nav.suppliers": {"bg": "Доставчици", "en": "Suppliers"},
    "nav.categories": {"bg": "Категории", "en": "Categories"},
    "nav.reports": {"bg": "Отчети", "en": "Reports"},
    "nav.users": {"bg": "Потребители", "en": "Users"},
    "nav.new_product": {"bg": "+ Нов продукт", "en": "+ New Product"},

    "auth.username": {"bg": "Потребителско име", "en": "Username"},
    "auth.password": {"bg": "Парола", "en": "Password"},
    "auth.confirm_password": {"bg": "Потвърди паролата", "en": "Confirm password"},
    "auth.login_title": {"bg": "Вход", "en": "Sign in"},
    "auth.login_button": {"bg": "Вход", "en": "Sign in"},
    "auth.logout": {"bg": "Изход", "en": "Log out"},
    "auth.setup_title": {"bg": "Създаване на администраторски акаунт", "en": "Create the admin account"},
    "auth.setup_help": {
        "bg": "Все още няма потребители. Създайте първия администраторски акаунт, за да влезете.",
        "en": "No users exist yet. Create the first admin account to get started.",
    },
    "auth.create_admin": {"bg": "Създай администратор", "en": "Create admin"},
    "auth.error_missing_fields": {"bg": "Попълнете потребителско име и парола.", "en": "Enter a username and password."},
    "auth.error_password_mismatch": {"bg": "Паролите не съвпадат.", "en": "Passwords do not match."},
    "auth.error_invalid_credentials": {"bg": "Грешно потребителско име или парола.", "en": "Invalid username or password."},
    "auth.forbidden_title": {"bg": "Нямате достъп", "en": "Access denied"},
    "auth.forbidden_help": {
        "bg": "Нямате права за тази страница. Свържете се с администратор, ако смятате, че това е грешка.",
        "en": "You don't have permission to view this page. Contact an admin if you think this is a mistake.",
    },

    "role.admin": {"bg": "Администратор", "en": "Admin"},
    "role.sales": {"bg": "Продавач", "en": "Sales"},

    "users.heading": {"bg": "Потребители", "en": "Users"},
    "users.new": {"bg": "+ Нов потребител", "en": "+ New User"},
    "users.new_title": {"bg": "Нов потребител", "en": "New User"},
    "users.edit_title": {"bg": "Редактиране на потребител", "en": "Edit User"},
    "users.create": {"bg": "Създай потребител", "en": "Create User"},
    "users.col_role": {"bg": "Роля", "en": "Role"},
    "users.empty": {"bg": "Все още няма потребители.", "en": "No users yet."},
    "users.delete_confirm": {"bg": "Да изтрия ли този потребител?", "en": "Delete this user?"},
    "users.password_help": {
        "bg": "Оставете празно, за да запазите текущата парола.",
        "en": "Leave blank to keep the current password.",
    },

    "common.save": {"bg": "Запази промените", "en": "Save Changes"},
    "common.cancel": {"bg": "Отказ", "en": "Cancel"},
    "common.edit": {"bg": "Редактирай", "en": "Edit"},
    "common.delete": {"bg": "Изтрий", "en": "Delete"},
    "common.remove": {"bg": "Премахни", "en": "Remove"},
    "common.view": {"bg": "Преглед", "en": "View"},
    "common.apply": {"bg": "Приложи", "en": "Apply"},
    "common.prev": {"bg": "Предишна", "en": "Prev"},
    "common.next": {"bg": "Следваща", "en": "Next"},
    "common.name": {"bg": "Име", "en": "Name"},
    "common.status": {"bg": "Статус", "en": "Status"},
    "common.created": {"bg": "Създадена", "en": "Created"},
    "common.notes": {"bg": "Бележки", "en": "Notes"},
    "common.note": {"bg": "Бележка", "en": "Note"},
    "common.quantity": {"bg": "Количество", "en": "Quantity"},
    "common.description": {"bg": "Описание", "en": "Description"},
    "common.total_cost": {"bg": "Обща стойност", "en": "Total Cost"},
    "common.unit_cost": {"bg": "Единична цена", "en": "Unit Cost"},
    "common.date": {"bg": "Дата", "en": "Date"},

    "gender.Men": {"bg": "Мъже", "en": "Men"},
    "gender.Women": {"bg": "Жени", "en": "Women"},
    "gender.Unisex": {"bg": "Унисекс", "en": "Unisex"},

    "reason.received": {"bg": "Получено", "en": "Received"},
    "reason.sale": {"bg": "Продажба", "en": "Sale"},
    "reason.adjustment": {"bg": "Корекция", "en": "Adjustment"},
    "reason.initial_stock": {"bg": "Начална наличност", "en": "Initial stock"},

    "po_status.draft": {"bg": "Чернова", "en": "Draft"},
    "po_status.ordered": {"bg": "Поръчана", "en": "Ordered"},
    "po_status.partial": {"bg": "Частично получена", "en": "Partial"},
    "po_status.received": {"bg": "Получена", "en": "Received"},
    "po_status.cancelled": {"bg": "Отказана", "en": "Cancelled"},

    "badge.low": {"bg": "нисък", "en": "low"},
    "badge.ok": {"bg": "ОК", "en": "ok"},

    "products.gender_label": {"bg": "Пол", "en": "Gender"},
    "products.category_label": {"bg": "Категория", "en": "Category"},
    "products.select_item_hint": {
        "bg": "Изберете артикул от дървото вляво, за да видите подробности.",
        "en": "Select an item from the tree on the left to see its details.",
    },

    "product_form.edit_title": {"bg": "Редактиране на продукт", "en": "Edit Product"},
    "product_form.new_title": {"bg": "Нов продукт", "en": "New Product"},
    "product_form.style_code": {"bg": "Код на модел", "en": "Style Code"},
    "product_form.no_categories": {
        "bg": "Все още няма категории.",
        "en": "No categories yet.",
    },
    "product_form.sell_price": {"bg": "Продажна цена ($)", "en": "Sell Price ($)"},
    "product_form.sell_price_help": {
        "bg": "Цената, която плаща клиентът. Доставната цена от доставчици се задава отделно на страницата на продукта.",
        "en": "Price charged to customers. Cost from suppliers is set separately on the product page.",
    },
    "product_form.material": {"bg": "Състав на материала", "en": "Material composition"},
    "product_form.material_placeholder": {
        "bg": "напр. 80% памук, 20% полиестер",
        "en": "e.g. 80% cotton, 20% polyester",
    },
    "product_form.care": {"bg": "Инструкции за поддръжка", "en": "Care instructions"},
    "product_form.care_placeholder": {
        "bg": "напр. Пране на 30°C, не избелвайте",
        "en": "e.g. Machine wash 30°C, do not bleach",
    },
    "product_form.season": {"bg": "Сезон", "en": "Season"},
    "product_form.season_placeholder": {"bg": "напр. Пролет/Лято 2026", "en": "e.g. SS26"},
    "product_form.status": {"bg": "Статус", "en": "Status"},
    "product_status.active": {"bg": "Активен", "en": "Active"},
    "product_status.draft": {"bg": "Чернова", "en": "Draft"},
    "product_status.discontinued": {"bg": "Спрян от продажба", "en": "Discontinued"},
    "product_form.initial_stock": {"bg": "Начална наличност", "en": "Initial stock"},
    "product_form.initial_stock_help": {
        "bg": "Всеки ред е комбинация от размер и цвят. Оставете празно, за да пропуснете реда.",
        "en": "Each row is a size/colour combination. Leave a row blank to skip it.",
    },
    "product_form.color_placeholder": {"bg": "напр. Синьо", "en": "e.g. Blue"},
    "product_form.create": {"bg": "Създай продукт", "en": "Create Product"},

    "product_detail.stock_by_size": {"bg": "Наличност по размер и цвят", "en": "Stock by size & colour"},
    "product_detail.col_size": {"bg": "Размер", "en": "Size"},
    "product_detail.col_color": {"bg": "Цвят", "en": "Colour"},
    "product_detail.col_buy_price": {"bg": "Доставна цена", "en": "Buy price"},
    "product_detail.batches_heading": {"bg": "Партиди на доставка", "en": "Delivery Batches"},
    "product_detail.col_received_date": {"bg": "Дата на доставка", "en": "Received"},
    "product_detail.col_qty_received": {"bg": "Получено кол.", "en": "Qty Received"},
    "product_detail.col_qty_remaining": {"bg": "Оставащо кол.", "en": "Qty Remaining"},
    "product_detail.no_batches": {
        "bg": "Все още няма получени доставки за този продукт.",
        "en": "No deliveries received yet for this product.",
    },
    "product_detail.col_sku_barcode": {"bg": "SKU / баркод", "en": "SKU / barcode"},
    "product_detail.barcode_placeholder": {"bg": "Баркод (EAN/UPC)", "en": "Barcode (EAN/UPC)"},
    "product_detail.col_manual_adjustment": {"bg": "Ръчна корекция", "en": "Manual adjustment"},
    "product_detail.delta_placeholder": {"bg": "+/- кол.", "en": "+/- qty"},
    "product_detail.reason_placeholder": {
        "bg": "Причина (напр. повреда, преброяване)",
        "en": "Reason (e.g. damaged, recount)",
    },
    "product_detail.manual_help": {
        "bg": "Използвайте това само за ръчни корекции (повреда, преброяване). Зареждането на стока става през",
        "en": "Use this only for manual corrections (damage, recounts). Restocking goes through",
    },
    "product_detail.manual_help_2": {
        "bg": "продажбите на клиенти - през",
        "en": "customer sales go through",
    },
    "product_detail.add_variant": {"bg": "Добави размер/цвят", "en": "Add size/colour"},
    "product_detail.initial_qty": {"bg": "Начално количество", "en": "Initial qty"},
    "product_detail.attributes_heading": {"bg": "Допълнителни характеристики", "en": "Attributes"},
    "product_detail.col_attribute": {"bg": "Характеристика", "en": "Attribute"},
    "product_detail.col_value": {"bg": "Стойност", "en": "Value"},
    "product_detail.no_attributes": {
        "bg": "Все още няма добавени характеристики (напр. кройка, десен).",
        "en": "No attributes added yet (e.g. fit, pattern).",
    },
    "product_detail.attribute_key_placeholder": {"bg": "напр. Кройка", "en": "e.g. Fit"},
    "product_detail.attribute_value_placeholder": {"bg": "напр. Свободна", "en": "e.g. Oversized"},
    "product_detail.add_attribute": {"bg": "Добави характеристика", "en": "Add attribute"},
    "product_detail.suppliers_heading": {"bg": "Доставчици", "en": "Suppliers"},
    "product_detail.col_supplier": {"bg": "Доставчик", "en": "Supplier"},
    "product_detail.col_cost_price": {"bg": "Доставна цена", "en": "Cost Price"},
    "product_detail.col_supplier_sku": {"bg": "SKU на доставчика", "en": "Supplier SKU"},
    "product_detail.no_suppliers_linked": {
        "bg": "Все още няма свързани доставчици.",
        "en": "No suppliers linked yet.",
    },
    "product_detail.add_supplier": {"bg": "Добави доставчик", "en": "Add supplier"},
    "product_detail.link_supplier": {"bg": "Свържи доставчик", "en": "Link Supplier"},
    "product_detail.no_suppliers_exist": {
        "bg": "Все още няма доставчици.",
        "en": "No suppliers exist yet.",
    },
    "product_detail.add_one": {"bg": "Добавете един", "en": "Add one"},
    "product_detail.recent_movements": {"bg": "Скорошни движения на склад", "en": "Recent stock movements"},
    "product_detail.col_when": {"bg": "Кога", "en": "When"},
    "product_detail.col_change": {"bg": "Промяна", "en": "Change"},
    "product_detail.col_reason": {"bg": "Причина", "en": "Reason"},
    "product_detail.no_movements": {"bg": "Все още няма движения на склад.", "en": "No stock movements yet."},
    "product_detail.delete_confirm": {
        "bg": "Да изтрия ли този продукт и цялата му история на наличности?",
        "en": "Delete this product and all its stock history?",
    },
    "product_detail.remove_supplier_confirm": {
        "bg": "Да премахна ли този доставчик?",
        "en": "Remove this supplier link?",
    },

    "suppliers.heading": {"bg": "Доставчици", "en": "Suppliers"},
    "suppliers.new": {"bg": "+ Нов доставчик", "en": "+ New Supplier"},
    "suppliers.col_contact": {"bg": "Контакт", "en": "Contact"},
    "suppliers.col_phone": {"bg": "Телефон", "en": "Phone"},
    "suppliers.col_email": {"bg": "Имейл", "en": "Email"},
    "suppliers.empty": {"bg": "Все още няма доставчици.", "en": "No suppliers yet."},
    "suppliers.add_first": {"bg": "Добавете първия си доставчик", "en": "Add your first supplier"},
    "suppliers.search_label": {"bg": "Търсене", "en": "Search"},
    "suppliers.search_placeholder": {"bg": "Име на доставчик", "en": "Supplier name"},

    "supplier_form.edit_title": {"bg": "Редактиране на доставчик", "en": "Edit Supplier"},
    "supplier_form.new_title": {"bg": "Нов доставчик", "en": "New Supplier"},
    "supplier_form.contact_name": {"bg": "Име за контакт", "en": "Contact Name"},
    "supplier_form.phone": {"bg": "Телефон", "en": "Phone"},
    "supplier_form.email": {"bg": "Имейл", "en": "Email"},
    "supplier_form.address": {"bg": "Адрес", "en": "Address"},
    "supplier_form.create": {"bg": "Създай доставчик", "en": "Create Supplier"},

    "supplier_detail.new_po": {"bg": "+ Нова поръчка за доставка", "en": "+ New Purchase Order"},
    "supplier_detail.delete_confirm": {"bg": "Да изтрия ли този доставчик?", "en": "Delete this supplier?"},
    "supplier_detail.products_supplied": {"bg": "Доставяни продукти", "en": "Products supplied"},
    "supplier_detail.col_product": {"bg": "Продукт", "en": "Product"},
    "supplier_detail.no_products_linked": {
        "bg": "Все още няма свързани продукти. Свържете този доставчик от страницата на продукт.",
        "en": "No products linked yet. Link this supplier from a product's page.",
    },
    "supplier_detail.purchase_orders": {"bg": "Поръчки за доставка", "en": "Purchase orders"},
    "supplier_detail.no_pos": {"bg": "Все още няма поръчки за доставка.", "en": "No purchase orders yet."},

    "po.heading": {"bg": "Поръчки за доставка", "en": "Purchase Orders"},
    "po.new": {"bg": "+ Нова поръчка за доставка", "en": "+ New Purchase Order"},
    "po.col_number": {"bg": "№", "en": "#"},
    "po.col_supplier": {"bg": "Доставчик", "en": "Supplier"},
    "po.empty": {"bg": "Все още няма поръчки за доставка.", "en": "No purchase orders yet."},
    "po.create_first": {"bg": "Създайте първата", "en": "Create your first one"},
    "po.search_supplier": {"bg": "Търсене по доставчик", "en": "Search by supplier"},
    "po.search_supplier_placeholder": {"bg": "Име на доставчик", "en": "Supplier name"},
    "po.new_title": {"bg": "Нова поръчка за доставка", "en": "New Purchase Order"},
    "po.choose_supplier": {"bg": "Изберете доставчик…", "en": "Choose a supplier…"},
    "po.line_items_for": {"bg": "Артикули за {supplier}", "en": "Line items for {supplier}"},
    "po.col_product_size": {"bg": "Продукт / Размер", "en": "Product / Size"},
    "po.col_unit_cost_dollar": {"bg": "Единична цена ($)", "en": "Unit Cost ($)"},
    "po.create": {"bg": "Създай поръчка", "en": "Create Purchase Order"},
    "po.detail_heading": {"bg": "Поръчка за доставка №{id}", "en": "Purchase Order #{id}"},
    "po.supplier_label": {"bg": "Доставчик", "en": "Supplier"},
    "po.mark_ordered": {"bg": "Маркирай като поръчана", "en": "Mark as Ordered"},
    "po.cancel_order": {"bg": "Откажи поръчката", "en": "Cancel Order"},
    "po.cancel_confirm": {"bg": "Да отменя ли тази поръчка за доставка?", "en": "Cancel this purchase order?"},
    "po.line_items": {"bg": "Артикули", "en": "Line items"},
    "po.col_ordered": {"bg": "Поръчано", "en": "Ordered"},
    "po.col_received": {"bg": "Получено", "en": "Received"},
    "po.col_remaining": {"bg": "Оставащо", "en": "Remaining"},
    "po.total_cost_label": {"bg": "Обща стойност:", "en": "Total cost:"},
    "po.receive_stock": {"bg": "Получаване на стока", "en": "Receive stock"},
    "po.col_receive_now": {"bg": "Получи сега", "en": "Receive now"},
    "po.receive_button": {"bg": "Получи стока", "en": "Receive Stock"},

    "sell.title": {"bg": "Нова продажба", "en": "New Sale"},
    "sell.search_products": {"bg": "Търсене на продукти", "en": "Search products"},
    "sell.search_placeholder": {"bg": "Търсене по име, SKU или разгледайте по категория", "en": "Search by name, SKU, or browse by category"},
    "sell.cart": {"bg": "Количка", "en": "Cart"},
    "sell.col_item": {"bg": "Артикул", "en": "Item"},
    "sell.col_unit_price": {"bg": "Единична цена", "en": "Unit Price"},
    "sell.col_line_total": {"bg": "Обща сума", "en": "Line Total"},
    "sell.total_label": {"bg": "Общо:", "en": "Total:"},
    "sell.note_placeholder": {"bg": "По желание (напр. име на клиент)", "en": "Optional note (e.g. customer name)"},
    "sell.complete_sale": {"bg": "Приключи продажбата", "en": "Complete Sale"},
    "sell.view_history": {"bg": "Виж всички продажби", "en": "View all sales"},
    "sell.recent_sales": {"bg": "Скорошни продажби", "en": "Recent Sales"},
    "sell.js_in_stock": {"bg": "в наличност", "en": "in stock"},
    "sell.js_remove": {"bg": "Премахни", "en": "Remove"},
    "sell.js_no_items": {"bg": "Няма артикули в тази категория.", "en": "No items in this category."},
    "sell.js_browse_hint": {"bg": "Разгледайте по категория", "en": "Browse by category"},
    "sell.js_uncategorized": {"bg": "Без категория", "en": "Uncategorized"},
    "sell.js_empty_cart_error": {
        "bg": "Добавете поне един артикул в количката, преди да приключите продажбата.",
        "en": "Add at least one item to the cart before completing the sale.",
    },

    "sales_history.heading": {"bg": "История на продажбите", "en": "Sales History"},
    "sales_history.new_sale": {"bg": "+ Нова продажба", "en": "+ New Sale"},
    "sales_history.col_items": {"bg": "Артикули", "en": "Items"},
    "sales_history.col_total": {"bg": "Общо", "en": "Total"},
    "sales_history.col_profit": {"bg": "Печалба", "en": "Profit"},
    "sales_history.receipt": {"bg": "Разписка", "en": "Receipt"},
    "sales_history.empty": {"bg": "Все още няма регистрирани продажби.", "en": "No sales recorded yet."},
    "sales_history.search_label": {"bg": "Търсене", "en": "Search"},
    "sales_history.search_placeholder": {
        "bg": "Продукт или бележка",
        "en": "Product or note",
    },
    "sales_history.page_of": {
        "bg": "Страница {page} от {total_pages}",
        "en": "Page {page} of {total_pages}",
    },

    "receipt.heading": {"bg": "Продажба №{id}", "en": "Sale #{id}"},
    "receipt.total_label": {"bg": "Общо:", "en": "Total:"},
    "receipt.cost_label": {"bg": "Себестойност:", "en": "Cost:"},
    "receipt.profit_label": {"bg": "Печалба:", "en": "Profit:"},
    "receipt.back": {"bg": "Обратно към историята на продажбите", "en": "Back to Sales History"},

    "reports.date_range": {"bg": "Период", "en": "Date range"},
    "reports.today": {"bg": "Днес", "en": "Today"},
    "reports.last_7": {"bg": "Последните 7 дни", "en": "Last 7 days"},
    "reports.last_30": {"bg": "Последните 30 дни", "en": "Last 30 days"},
    "reports.custom": {"bg": "Персонализиран", "en": "Custom"},
    "reports.from": {"bg": "От", "en": "From"},
    "reports.to": {"bg": "До", "en": "To"},
    "reports.revenue": {"bg": "Приходи", "en": "Revenue"},
    "reports.cost": {"bg": "Разход", "en": "Cost"},
    "reports.gross_profit": {"bg": "Брутна печалба", "en": "Gross Profit"},
    "reports.margin": {"bg": "Марж", "en": "Margin"},
    "reports.inventory_value": {"bg": "Стойност на наличностите", "en": "Inventory Value"},
    "reports.revenue_by_day": {"bg": "Приходи по дни", "en": "Revenue by day"},
    "reports.no_sales_range": {"bg": "Няма продажби в този период.", "en": "No sales in this range."},
    "reports.top_products": {"bg": "Най-продавани продукти", "en": "Top selling products"},
    "reports.col_qty_sold": {"bg": "Продадено количество", "en": "Qty Sold"},

    "categories.heading": {"bg": "Категории", "en": "Categories"},
    "categories.new": {"bg": "+ Нова категория", "en": "+ New Category"},
    "categories.empty": {"bg": "Все още няма категории.", "en": "No categories yet."},
    "categories.add_first": {"bg": "Добавете първата си категория", "en": "Add your first category"},
    "categories.delete_confirm": {"bg": "Да изтрия ли тази категория?", "en": "Delete this category?"},
    "categories.edit_title": {"bg": "Редактиране на категория", "en": "Edit Category"},
    "categories.new_title": {"bg": "Нова категория", "en": "New Category"},
    "categories.parent": {"bg": "Родителска категория", "en": "Parent category"},
    "categories.top_level": {"bg": "— Основно ниво —", "en": "— Top level —"},
    "categories.create": {"bg": "Създай категория", "en": "Create Category"},
}


def get_lang(request: Request) -> str:
    lang = request.cookies.get(LANG_COOKIE)
    if lang in SUPPORTED_LANGS:
        return lang
    return DEFAULT_LANG


def translator(lang: str):
    def t(key: str, **kwargs) -> str:
        entry = TRANSLATIONS.get(key)
        if not entry:
            return key
        text = entry.get(lang) or entry.get(DEFAULT_LANG) or key
        if kwargs:
            text = text.format(**kwargs)
        return text

    return t
