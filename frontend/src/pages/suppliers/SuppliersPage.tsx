import { useState } from "react";
import type { FormEvent } from "react";

import { useMe } from "../../api/auth";
import { ApiError } from "../../api/client";
import { useCreateSupplier, useSuppliers, useUpdateSupplier } from "../../api/suppliers";

export default function SuppliersPage() {
  const { data: me } = useMe();
  const canManage = !!me?.permissions.includes("suppliers.manage_suppliers");
  const { data: suppliers, isLoading } = useSuppliers();
  const [formOpen, setFormOpen] = useState(false);

  return (
    <div className="p-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold text-slate-900">Suppliers</h1>
        {canManage && (
          <button
            onClick={() => setFormOpen((o) => !o)}
            className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-700"
          >
            + Supplier
          </button>
        )}
      </div>

      {formOpen && <NewSupplierForm onClose={() => setFormOpen(false)} />}

      {isLoading && <p className="text-sm text-slate-500">Loading…</p>}
      {suppliers && suppliers.length === 0 && (
        <p className="text-sm text-slate-500">No suppliers yet.</p>
      )}
      {suppliers && suppliers.length > 0 && (
        <table className="w-full max-w-3xl text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-left text-xs text-slate-500">
              <th className="py-1 pr-2">Name</th>
              <th className="py-1 pr-2">Contact</th>
              <th className="py-1 pr-2">Email</th>
              <th className="py-1 pr-2">Phone</th>
              <th className="py-1"></th>
            </tr>
          </thead>
          <tbody>
            {suppliers.map((supplier) => (
              <SupplierRow key={supplier.id} supplier={supplier} canManage={canManage} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function SupplierRow({
  supplier,
  canManage,
}: {
  supplier: { id: number; name: string; contact_name: string; email: string; phone: string; is_active: boolean };
  canManage: boolean;
}) {
  const [editing, setEditing] = useState(false);
  const update = useUpdateSupplier();
  const [contactName, setContactName] = useState(supplier.contact_name);
  const [email, setEmail] = useState(supplier.email);
  const [phone, setPhone] = useState(supplier.phone);

  if (editing) {
    return (
      <tr className="border-b border-slate-100 bg-slate-50">
        <td className="py-1.5 pr-2 font-medium">{supplier.name}</td>
        <td className="py-1.5 pr-2">
          <input value={contactName} onChange={(e) => setContactName(e.target.value)}
                 className="w-full rounded border border-slate-300 px-1 py-0.5 text-sm" />
        </td>
        <td className="py-1.5 pr-2">
          <input value={email} onChange={(e) => setEmail(e.target.value)}
                 className="w-full rounded border border-slate-300 px-1 py-0.5 text-sm" />
        </td>
        <td className="py-1.5 pr-2">
          <input value={phone} onChange={(e) => setPhone(e.target.value)}
                 className="w-full rounded border border-slate-300 px-1 py-0.5 text-sm" />
        </td>
        <td className="py-1.5 text-right text-xs">
          <button
            onClick={() =>
              update.mutate(
                { supplierId: supplier.id, input: { contact_name: contactName, email, phone } },
                { onSuccess: () => setEditing(false) },
              )
            }
            className="mr-2 text-slate-600 underline hover:text-slate-900"
          >
            Save
          </button>
          <button onClick={() => setEditing(false)} className="text-slate-400 hover:text-slate-700">Cancel</button>
        </td>
      </tr>
    );
  }

  return (
    <tr className="border-b border-slate-100">
      <td className="py-1.5 pr-2 font-medium">{supplier.name}</td>
      <td className="py-1.5 pr-2 text-slate-600">{supplier.contact_name || "—"}</td>
      <td className="py-1.5 pr-2 text-slate-600">{supplier.email || "—"}</td>
      <td className="py-1.5 pr-2 text-slate-600">{supplier.phone || "—"}</td>
      <td className="py-1.5 text-right">
        {canManage && (
          <button onClick={() => setEditing(true)} className="text-xs text-slate-600 underline hover:text-slate-900">
            Edit
          </button>
        )}
      </td>
    </tr>
  );
}

function NewSupplierForm({ onClose }: { onClose: () => void }) {
  const createSupplier = useCreateSupplier();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    createSupplier.mutate(
      { name, email, phone },
      {
        onSuccess: () => onClose(),
        onError: (err) => setError(err instanceof ApiError ? err.message : "Could not create supplier."),
      },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="mb-4 grid max-w-lg grid-cols-3 gap-2 rounded border border-slate-200 bg-slate-50 p-3">
      <input autoFocus value={name} onChange={(e) => setName(e.target.value)} placeholder="Name"
             className="col-span-3 rounded border border-slate-300 px-2 py-1 text-sm" />
      <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email"
             className="rounded border border-slate-300 px-2 py-1 text-sm" />
      <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Phone"
             className="rounded border border-slate-300 px-2 py-1 text-sm" />
      <div className="flex items-center gap-2">
        <button type="submit" disabled={!name || createSupplier.isPending}
                className="rounded bg-slate-900 px-3 py-1 text-xs text-white hover:bg-slate-700 disabled:opacity-50">
          Create
        </button>
        <button type="button" onClick={onClose} className="text-xs text-slate-500 hover:text-slate-800">Cancel</button>
      </div>
      {error && <p className="col-span-3 text-xs text-red-600">{error}</p>}
    </form>
  );
}
