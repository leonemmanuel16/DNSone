"use client";

import { useEffect, useState, FormEvent } from "react";
import { apiCustomers, ApiError } from "@/lib/api";
import type { Customer } from "@/lib/types";

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<Partial<Customer>>({ name: "", tax_id: "", email: "", phone: "" });
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const page = await apiCustomers.list();
      setCustomers(page.items);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    try {
      await apiCustomers.create(form);
      setShowForm(false);
      setForm({ name: "", tax_id: "", email: "", phone: "" });
      load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error");
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-light"
        >
          {showForm ? "Cancelar" : "+ Nuevo cliente"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={onCreate} className="mb-6 rounded border border-gray-200 bg-white p-4">
          <div className="grid grid-cols-2 gap-3">
            <input required placeholder="Nombre / Razón social" value={form.name || ""}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="rounded border border-gray-300 px-3 py-2" />
            <input placeholder="RFC" value={form.tax_id || ""}
              onChange={(e) => setForm({ ...form, tax_id: e.target.value })}
              className="rounded border border-gray-300 px-3 py-2" />
            <input type="email" placeholder="Email" value={form.email || ""}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="rounded border border-gray-300 px-3 py-2" />
            <input placeholder="Teléfono" value={form.phone || ""}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              className="rounded border border-gray-300 px-3 py-2" />
          </div>
          <button type="submit" className="mt-3 rounded bg-brand px-4 py-2 text-sm text-white">Crear</button>
        </form>
      )}

      {error && <div className="mb-4 rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <div className="overflow-x-auto rounded border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-600">
            <tr>
              <th className="px-4 py-2">Nombre</th>
              <th className="px-4 py-2">RFC</th>
              <th className="px-4 py-2">Email</th>
              <th className="px-4 py-2">Teléfono</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={4} className="p-6 text-center text-gray-500">Cargando...</td></tr>
            ) : customers.length === 0 ? (
              <tr><td colSpan={4} className="p-6 text-center text-gray-500">Sin clientes</td></tr>
            ) : customers.map((c) => (
              <tr key={c.id} className="border-t border-gray-100">
                <td className="px-4 py-2 font-medium">{c.name}</td>
                <td className="px-4 py-2 font-mono text-xs">{c.tax_id || "—"}</td>
                <td className="px-4 py-2">{c.email || "—"}</td>
                <td className="px-4 py-2">{c.phone || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
