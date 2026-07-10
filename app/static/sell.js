document.addEventListener("DOMContentLoaded", function () {
  var catalog = JSON.parse(document.getElementById("catalog-data").textContent);
  var categoryTree = JSON.parse(document.getElementById("category-tree-data").textContent);
  var i18n = JSON.parse(document.getElementById("i18n-data").textContent);
  var cart = [];

  var searchInput = document.getElementById("search-input");
  var resultsEl = document.getElementById("search-results");
  var cartBody = document.getElementById("cart-body");
  var totalEl = document.getElementById("cart-total");
  var form = document.getElementById("sale-form");
  var hiddenInputs = document.getElementById("hidden-inputs");
  var errorEl = document.getElementById("cart-error");

  var itemsByCategory = {};
  catalog.forEach(function (item) {
    var key = item.category_id === null || item.category_id === undefined ? "none" : String(item.category_id);
    if (!itemsByCategory[key]) itemsByCategory[key] = [];
    itemsByCategory[key].push(item);
  });

  function hiddenField(name, value) {
    var input = document.createElement("input");
    input.type = "hidden";
    input.name = name;
    input.value = value;
    return input;
  }

  function renderItemRow(item) {
    var row = document.createElement("div");
    row.className = "search-result" + (item.stock <= 0 ? " disabled" : "");
    row.textContent =
      item.label + " — $" + item.price.toFixed(2) + " (" + item.stock + " " + i18n.in_stock + ")";
    if (item.stock > 0) {
      row.addEventListener("click", function () {
        addToCart(item);
      });
    }
    return row;
  }

  function renderBrowseTree() {
    resultsEl.innerHTML = "";

    var hint = document.createElement("div");
    hint.className = "dd-hint muted";
    hint.textContent = i18n.browse_hint;
    resultsEl.appendChild(hint);

    var tree = categoryTree;
    var uncategorized = itemsByCategory["none"] || [];
    if (uncategorized.length) {
      tree = tree.concat([{ id: "none", name: i18n.uncategorized || "—", children: [] }]);
    }

    CategoryTree.render(resultsEl, tree, itemsByCategory, renderItemRow, {
      emptyText: i18n.no_items,
    });

    resultsEl.classList.add("open");
  }

  function renderSearchResults() {
    var q = searchInput.value.trim().toLowerCase();
    resultsEl.innerHTML = "";

    var matches = catalog
      .filter(function (item) {
        return (
          item.label.toLowerCase().indexOf(q) !== -1 ||
          item.sku.toLowerCase().indexOf(q) !== -1
        );
      })
      .slice(0, 20);

    if (matches.length === 0) {
      var empty = document.createElement("p");
      empty.className = "muted dd-empty";
      empty.textContent = i18n.no_items;
      resultsEl.appendChild(empty);
    } else {
      matches.forEach(function (item) {
        resultsEl.appendChild(renderItemRow(item));
      });
    }
    resultsEl.classList.add("open");
  }

  function renderDropdown() {
    if (searchInput.value.trim()) {
      renderSearchResults();
    } else {
      renderBrowseTree();
    }
  }

  function closeDropdown() {
    resultsEl.classList.remove("open");
    resultsEl.innerHTML = "";
  }

  function addToCart(item) {
    var existing = cart.find(function (l) {
      return l.variant_id === item.variant_id;
    });
    if (existing) {
      if (existing.qty < item.stock) existing.qty += 1;
    } else {
      cart.push({
        variant_id: item.variant_id,
        label: item.label,
        price: item.price,
        stock: item.stock,
        qty: 1,
      });
    }
    searchInput.value = "";
    errorEl.textContent = "";
    closeDropdown();
    renderCart();
  }

  function renderCart() {
    cartBody.innerHTML = "";
    var total = 0;

    cart.forEach(function (line, idx) {
      var tr = document.createElement("tr");

      var nameTd = document.createElement("td");
      nameTd.textContent = line.label;
      tr.appendChild(nameTd);

      var qtyTd = document.createElement("td");
      var qtyInput = document.createElement("input");
      qtyInput.type = "number";
      qtyInput.min = "1";
      qtyInput.max = String(line.stock);
      qtyInput.value = line.qty;
      qtyInput.style.width = "70px";
      qtyInput.addEventListener("input", function () {
        var v = parseInt(qtyInput.value || "0", 10);
        line.qty = Math.max(1, Math.min(v || 1, line.stock));
        renderCart();
      });
      qtyTd.appendChild(qtyInput);
      tr.appendChild(qtyTd);

      var priceTd = document.createElement("td");
      var priceInput = document.createElement("input");
      priceInput.type = "number";
      priceInput.step = "0.01";
      priceInput.min = "0";
      priceInput.value = line.price.toFixed(2);
      priceInput.style.width = "90px";
      priceInput.addEventListener("input", function () {
        line.price = parseFloat(priceInput.value || "0");
        renderCart();
      });
      priceTd.appendChild(priceInput);
      tr.appendChild(priceTd);

      var lineTotalTd = document.createElement("td");
      var lineTotal = line.qty * line.price;
      lineTotalTd.textContent = "$" + lineTotal.toFixed(2);
      tr.appendChild(lineTotalTd);
      total += lineTotal;

      var removeTd = document.createElement("td");
      var removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "button secondary";
      removeBtn.textContent = i18n.remove;
      removeBtn.addEventListener("click", function () {
        cart.splice(idx, 1);
        renderCart();
      });
      removeTd.appendChild(removeBtn);
      tr.appendChild(removeTd);

      cartBody.appendChild(tr);
    });

    totalEl.textContent = "$" + total.toFixed(2);
  }

  searchInput.addEventListener("input", renderDropdown);
  searchInput.addEventListener("focus", renderDropdown);

  // Keep the dropdown open while interacting with it (mousedown fires before
  // blur, so preventing its default stops the input from losing focus).
  resultsEl.addEventListener("mousedown", function (e) {
    e.preventDefault();
  });

  document.addEventListener("click", function (e) {
    if (e.target !== searchInput && !resultsEl.contains(e.target)) {
      closeDropdown();
    }
  });

  form.addEventListener("submit", function (e) {
    if (cart.length === 0) {
      e.preventDefault();
      errorEl.textContent = i18n.empty_cart_error;
      return;
    }
    hiddenInputs.innerHTML = "";
    cart.forEach(function (line) {
      hiddenInputs.appendChild(hiddenField("variant_ids", line.variant_id));
      hiddenInputs.appendChild(hiddenField("quantities", line.qty));
      hiddenInputs.appendChild(hiddenField("unit_prices", line.price));
    });
  });
});
