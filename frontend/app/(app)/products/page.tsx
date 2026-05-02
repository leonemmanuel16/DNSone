"use client";

import { useEffect, useState } from "react";
import { apiProducts, apiSync, ApiError } from "@/lib/api";
import type { Product } from "@/lib/types";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const page = await apiProducts.list(q || undefined);
      setProducts(page.items);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error cargando productos");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function syncFromBind() {
    setSyncing(true);
    try {
      await apiSync.triggerProducts();
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error en sync");
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Productos</h1>
          <p className="text-sm text-gray-500">Catálogo sincronizado con BIND</p>
        </div>
        <button
          onClick={syncFromBind}
          disabled={syncing}
          className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-light disabled:opacity-60"
        >
          {syncing ? "Sincronizando..." : "↻ Sync con BIND"}
        </button>
      </div>

      <div className="mb-4 flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          placeholder="Buscar por SKU, nombre o marca..."
          className="flex-1 rounded border border-gray-300 px-3 py-2"
        />
        <button onClick={load} className="rounded bg-gray-200 px-4 py-2 text-sm">
          Buscar
        </button>
      </div>

      {error && <div className="mb-4 rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <div className="overflow-x-auto rounded border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-600">
            <tr>
              <th className="px-4 py-2">SKU</th>
              <th className="px-4 py-2">Nombre</th>
              <th className="px-4 py-2">Marca</th>
              <th className="px-4 py-2">Categoría</th>
              <th className="px-4 py-2 text-right">Precio USD</th>
              <th className="px-4 py-2">BIND</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="p-6 text-center text-gray-500">Cargando...</td></tr>
            ) : products.length === 0 ? (
              <tr><td colSpan={6} className="p-6 text-center text-gray-500">Sin productos. Haz click en &quot;Sync con BIND&quot;.</td></tr>
            ) : (
              products.map((p) => (
                <tr key={p.id} className="border-t border-gray-100">
                  <td className="px-4 py-2 font-mono text-xs">{p.sku}</td>
                  <td className="px-4 py-2">{p.name}</td>
                  <td className="px-4 py-2">{p.brand || "—"}</td>
                  <td className="px-4 py-2">{p.category || "—"}</td>
                  <td className="px-4 py-2 text-right">{p.list_price_usd ? `$${p.list_price_usd}` : "—"}</td>
                  <td className="px-4 py-2 text-xs text-gray-500">{p.bind_product_id || "—"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
