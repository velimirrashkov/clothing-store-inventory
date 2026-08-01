import { useState } from "react";
import type { FormEvent } from "react";

import { useCategories, useCreateCategory } from "../../api/catalog";
import { ApiError } from "../../api/client";

export function NewCategoryForm({ onClose }: { onClose: () => void }) {
  const { data: categories } = useCategories();
  const createCategory = useCreateCategory();
  const [name, setName] = useState("");
  const [parent, setParent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    createCategory.mutate(
      { name, parent: parent ? Number(parent) : null },
      {
        onSuccess: () => onClose(),
        onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create category."),
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2 border-b border-slate-200 p-3">
      <input
        autoFocus
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Category name"
        className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
      />
      <select
        value={parent}
        onChange={(e) => setParent(e.target.value)}
        className="w-full rounded border border-slate-300 px-2 py-1 text-sm"
      >
        <option value="">No parent (top level)</option>
        {categories?.map((c) => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </select>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={!name || createCategory.isPending}
                className="rounded bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50">
          Create
        </button>
        <button type="button" onClick={onClose} className="text-xs text-slate-500 hover:text-slate-800">
          Cancel
        </button>
      </div>
    </form>
  );
}
