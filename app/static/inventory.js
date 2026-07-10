document.addEventListener("DOMContentLoaded", function () {
  var catalog = JSON.parse(document.getElementById("catalog-data").textContent);
  var categoryTree = JSON.parse(document.getElementById("category-tree-data").textContent);

  var treeContainer = document.getElementById("inventory-tree");
  var detailPanel = document.getElementById("inventory-detail");

  var itemsByCategory = {};
  catalog.forEach(function (item) {
    var key = item.category_id === null || item.category_id === undefined ? "none" : String(item.category_id);
    if (!itemsByCategory[key]) itemsByCategory[key] = [];
    itemsByCategory[key].push(item);
  });

  var selectedItemRow = null;
  var selectedCategoryHeader = null;

  function selectItemRow(row) {
    if (selectedItemRow) selectedItemRow.classList.remove("selected");
    row.classList.add("selected");
    selectedItemRow = row;
  }

  function selectCategoryHeader(header) {
    if (selectedCategoryHeader) selectedCategoryHeader.classList.remove("selected");
    if (header) header.classList.add("selected");
    selectedCategoryHeader = header;
  }

  function renderItemRow(item) {
    var row = document.createElement("div");
    row.className = "tree-item-row";
    row.textContent = item.name;
    row.addEventListener("click", function () {
      selectItemRow(row);
      var categoryKey = item.category_id === null || item.category_id === undefined ? "none" : String(item.category_id);
      selectCategoryHeader(nodesById[categoryKey] ? nodesById[categoryKey].header : null);
      loadDetail(item.id);
    });
    return row;
  }

  function loadDetail(productId) {
    detailPanel.innerHTML = '<p class="muted">…</p>';
    fetch("/products/" + productId + "/panel")
      .then(function (resp) {
        if (!resp.ok) throw new Error("Failed to load");
        return resp.text();
      })
      .then(function (html) {
        detailPanel.innerHTML = html;
      })
      .catch(function () {
        detailPanel.innerHTML = '<p class="muted">Could not load this item.</p>';
      });
  }

  var nodesById = CategoryTree.render(treeContainer, categoryTree, itemsByCategory, renderItemRow);

  var uncategorized = itemsByCategory["none"] || [];
  if (uncategorized.length) {
    var extra = CategoryTree.render(
      treeContainer,
      [{ id: "none", name: "—", children: [] }],
      itemsByCategory,
      renderItemRow
    );
    Object.assign(nodesById, extra);
  }
});
