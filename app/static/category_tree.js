// Shared collapsible category tree renderer, used by both the Sell page
// (dropdown browse) and the Inventory page (persistent master-detail tree).
//
// Usage:
//   var nodesById = CategoryTree.render(containerEl, treeNodes, itemsByCategory, function (item) {
//     return someRowElement; // must attach its own click handler
//   }, { emptyText: "..." });
//
// `itemsByCategory` maps String(categoryId) -> array of items belonging
// directly to that category. Item rows are only built the first time a node
// is expanded, so trees with many categories/items stay cheap to render.
//
// Returns a map of String(categoryId) -> { li, header } for every node built,
// so callers can highlight a node (e.g. the one containing a selected item).
window.CategoryTree = (function () {
  function countRecursive(node, itemsByCategory) {
    var count = (itemsByCategory[String(node.id)] || []).length;
    node.children.forEach(function (child) {
      count += countRecursive(child, itemsByCategory);
    });
    return count;
  }

  function render(containerEl, treeNodes, itemsByCategory, renderItemFn, options) {
    options = options || {};
    var nodesById = {};

    function renderNode(node, depth) {
      var itemsForNode = itemsByCategory[String(node.id)] || [];
      var totalCount = itemsForNode.length;
      node.children.forEach(function (child) {
        totalCount += countRecursive(child, itemsByCategory);
      });

      var li = document.createElement("li");
      li.className = "dd-node" + (depth === 0 ? " dd-node-root" : "");

      var header = document.createElement("div");
      header.className = "dd-node-header";

      var arrow = document.createElement("span");
      arrow.className = "dd-arrow";
      arrow.textContent = "▸";
      header.appendChild(arrow);

      var name = document.createElement("span");
      name.className = "dd-node-name";
      name.textContent = node.name;
      header.appendChild(name);

      var count = document.createElement("span");
      count.className = "dd-node-count";
      count.textContent = totalCount;
      header.appendChild(count);

      li.appendChild(header);
      nodesById[String(node.id)] = { li: li, header: header };

      var childrenWrap = document.createElement("div");
      childrenWrap.className = "dd-node-children";
      li.appendChild(childrenWrap);

      var built = false;
      header.addEventListener("click", function () {
        var isOpen = li.classList.toggle("open");
        if (isOpen && !built) {
          built = true;
          if (node.children.length) {
            var childUl = document.createElement("ul");
            childUl.className = "dd-tree";
            node.children.forEach(function (child) {
              childUl.appendChild(renderNode(child, depth + 1));
            });
            childrenWrap.appendChild(childUl);
          }
          itemsForNode.forEach(function (item) {
            childrenWrap.appendChild(renderItemFn(item));
          });
          if (!node.children.length && !itemsForNode.length && options.emptyText) {
            var empty = document.createElement("p");
            empty.className = "muted dd-empty";
            empty.textContent = options.emptyText;
            childrenWrap.appendChild(empty);
          }
        }
      });

      return li;
    }

    var ul = document.createElement("ul");
    ul.className = "dd-tree dd-tree-root";
    treeNodes.forEach(function (node) {
      ul.appendChild(renderNode(node, 0));
    });
    containerEl.appendChild(ul);

    return nodesById;
  }

  return { render: render };
})();
