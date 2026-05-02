"use client";

import { useEffect, useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { apiCustomers, apiProjects, ApiError } from "@/lib/api";
import type { Customer } from "@/lib/types";

export default function NewProjectPage() {
  const router = useRouter();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [name, setName] = useState("");
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [currency, setCurrency] = useState<"USD" | "MXN">("USD");
  const [exchangeRate, setExchangeRate] = useState("19.00");
  const [discountPct, setDiscountPct] = useState("0");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    apiCustomers.list().then((p) => setCustomers(p.items));
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!customerId) {
      setError("Selecciona un cliente");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const created = await apiProjects.create({
        name,
        customer_id: customerId,
        currency,
        exchange_rate: exchangeRate,
        discount_pct: discountPct,
        notes,
        items: [],
      });
      router.push(`/projects/${created.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Nueva cotización</h1>

      <form onSubmit={onSubmit} className="space-y-4 rounded border border-gray-200 bg-white p-6">
        <div>
          <label className="mb-1 block text-sm font-medium">Nombre del proyecto</label>
          <input
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ej. Renovación red corporativa cliente X"
            className="w-full rounded border border-gray-300 px-3 py-2"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Cliente</label>
          <select
            required
            value={customerId || ""}
            onChange={(e) => setCustomerId(Number(e.target.value))}
            className="w-full rounded border border-gray-300 px-3 py-2"
          >
            <option value="">— Seleccionar —</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>{c.name}{c.tax_id ? ` (${c.tax_id})` : ""}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="mb-1 block text-sm font-medium">Moneda</label>
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value as "USD" | "MXN")}
              className="w-full rounded border border-gray-300 px-3 py-2"
            >
              <option value="USD">USD</option>
              <option value="MXN">MXN</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">TC USD→MXN</label>
            <input
              value={exchangeRate}
              onChange={(e) => setExchangeRate(e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">Desc. global %</label>
            <input
              value={discountPct}
              onChange={(e) => setDiscountPct(e.target.value)}
              className="w-full rounded border border-gray-300 px-3 py-2"
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium">Notas</label>
          <textarea
            rows={3}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="w-full rounded border border-gray-300 px-3 py-2"
          />
        </div>

        {error && <div className="rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={submitting}
            className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-light disabled:opacity-60"
          >
            {submitting ? "Creando..." : "Crear cotización"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="rounded border border-gray-300 px-4 py-2 text-sm"
          >
            Cancelar
          </button>
        </div>
      </form>
    </div>
  );
}
