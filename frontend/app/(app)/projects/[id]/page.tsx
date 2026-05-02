"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiProducts, apiProjects, ApiError } from "@/lib/api";
import type { Product, Project, QuoteItem } from "@/lib/types";

export default function ProjectDetailPage() {
  const params = useParams<{ id: string }>();
  const projectId = Number(params?.id);

  const [project, setProject] = useState<Project | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form de nueva partida
  const [newItem, setNewItem] = useState<Partial<QuoteItem>>({
    sku: "", description: "", qty: "1", unit_cost: "0", unit_price: "0",
    discount_pct: "0", tax_pct: "16",
  });

  async function load() {
    try {
      const p = await apiProjects.get(projectId);
      setProject(p);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error cargando");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!projectId) return;
    load();
    apiProducts.list().then((p) => setProducts(p.items)).catch(() => {});
  }, [projectId]);

  function pickProduct(productId: number) {
    const p = products.find((x) => x.id === productId);
    if (!p) return;
    setNewItem((it) => ({
      ...it,
      product_id: productId,
      sku: p.sku,
      description: p.name,
      unit_price: String(p.list_price_usd ?? "0"),
      unit_cost: String(p.cost_usd ?? "0"),
    }));
  }

  async function addItem() {
    if (!project) return;
    setBusy("add");
    try {
      await apiProjects.addItem(project.id, newItem);
      setNewItem({ sku: "", description: "", qty: "1", unit_cost: "0", unit_price: "0", discount_pct: "0", tax_pct: "16" });
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error");
    } finally {
      setBusy(null);
    }
  }

  async function deleteItem(itemId: number) {
    if (!project || !confirm("¿Eliminar partida?")) return;
    setBusy("del" + itemId);
    try {
      await apiProjects.deleteItem(project.id, itemId);
      await load();
    } finally {
      setBusy(null);
    }
  }

  async function recalc() {
    if (!project) return;
    setBusy("recalc");
    try {
      await apiProjects.recalculate(project.id);
      await load();
    } finally {
      setBusy(null);
    }
  }

  async function pushBind() {
    if (!project || !confirm("¿Enviar esta cotización a BIND?")) return;
    setBusy("push");
    try {
      await apiProjects.pushToBind(project.id);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error");
    } finally {
      setBusy(null);
    }
  }

  if (loading) return <div className="text-gray-500">Cargando...</div>;
  if (!project) return <div className="text-red-700">{error || "No encontrada"}</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs text-gray-500">Folio interno</div>
          <h1 className="font-mono text-2xl font-bold text-brand">{project.code}</h1>
          <h2 className="mt-1 text-lg text-gray-800">{project.name}</h2>
          <p className="text-sm text-gray-500">
            Cliente: <strong>{project.customer?.name}</strong> · Estatus: <strong>{project.status}</strong>
            {project.bind_folio && (<> · Folio BIND: <strong className="text-brand-accent">{project.bind_folio}</strong></>)}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={recalc}
            disabled={busy === "recalc"}
            className="rounded border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
          >
            ↻ Recalcular
          </button>
          <a
            href={`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/v1/projects/${project.id}/pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded border border-gray-300 px-3 py-2 text-sm hover:bg-gray-50"
          >
            📄 PDF
          </a>
          <button
            onClick={pushBind}
            disabled={busy === "push" || project.items.length === 0}
            className="rounded bg-brand px-3 py-2 text-sm text-white hover:bg-brand-light disabled:opacity-60"
          >
            {project.bind_quote_id ? "↻ Re-enviar a BIND" : "Enviar a BIND"}
          </button>
        </div>
      </div>

      {error && <div className="rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      {/* Items */}
      <div className="rounded border border-gray-200 bg-white">
        <div className="border-b border-gray-200 px-4 py-3 font-medium">Partidas</div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-600">
            <tr>
              <th className="px-3 py-2">#</th>
              <th className="px-3 py-2">SKU</th>
              <th className="px-3 py-2">Descripción</th>
              <th className="px-3 py-2 text-right">Cant.</th>
              <th className="px-3 py-2 text-right">P. unit.</th>
              <th className="px-3 py-2 text-right">Desc.</th>
              <th className="px-3 py-2 text-right">Importe</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {project.items.length === 0 ? (
              <tr><td colSpan={8} className="p-6 text-center text-gray-500">Sin partidas — agrega abajo</td></tr>
            ) : project.items.map((it) => (
              <tr key={it.id} className="border-t border-gray-100">
                <td className="px-3 py-2">{it.position}</td>
                <td className="px-3 py-2 font-mono text-xs">{it.sku}</td>
                <td className="px-3 py-2">{it.description}</td>
                <td className="px-3 py-2 text-right">{Number(it.qty).toFixed(2)}</td>
                <td className="px-3 py-2 text-right">{Number(it.unit_price).toFixed(2)}</td>
                <td className="px-3 py-2 text-right">{Number(it.discount_pct).toFixed(2)}%</td>
                <td className="px-3 py-2 text-right font-medium">{Number(it.line_sale_total).toFixed(2)}</td>
                <td className="px-3 py-2 text-right">
                  <button
                    onClick={() => deleteItem(it.id)}
                    disabled={busy === "del" + it.id}
                    className="text-xs text-red-600 hover:underline"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Form nueva partida */}
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="grid grid-cols-12 gap-2 text-sm">
            <select
              className="col-span-3 rounded border border-gray-300 px-2 py-1.5"
              onChange={(e) => e.target.value && pickProduct(Number(e.target.value))}
              value={newItem.product_id || ""}
            >
              <option value="">— Producto del catálogo —</option>
              {products.map((p) => <option key={p.id} value={p.id}>{p.sku} — {p.name}</option>)}
            </select>
            <input className="col-span-2 rounded border border-gray-300 px-2 py-1.5" placeholder="SKU"
              value={newItem.sku || ""} onChange={(e) => setNewItem({ ...newItem, sku: e.target.value })} />
            <input className="col-span-3 rounded border border-gray-300 px-2 py-1.5" placeholder="Descripción"
              value={newItem.description || ""} onChange={(e) => setNewItem({ ...newItem, description: e.target.value })} />
            <input className="col-span-1 rounded border border-gray-300 px-2 py-1.5 text-right" placeholder="Cant"
              value={String(newItem.qty || "")} onChange={(e) => setNewItem({ ...newItem, qty: e.target.value })} />
            <input className="col-span-1 rounded border border-gray-300 px-2 py-1.5 text-right" placeholder="P.U."
              value={String(newItem.unit_price || "")} onChange={(e) => setNewItem({ ...newItem, unit_price: e.target.value })} />
            <input className="col-span-1 rounded border border-gray-300 px-2 py-1.5 text-right" placeholder="Desc%"
              value={String(newItem.discount_pct || "")} onChange={(e) => setNewItem({ ...newItem, discount_pct: e.target.value })} />
            <button onClick={addItem} disabled={busy === "add"}
              className="col-span-1 rounded bg-brand px-2 py-1.5 text-white hover:bg-brand-light disabled:opacity-60">
              + Agregar
            </button>
          </div>
        </div>
      </div>

      {/* Totales */}
      <div className="ml-auto w-96 rounded border border-gray-200 bg-white p-4 text-sm">
        <div className="flex justify-between py-1">
          <span className="text-gray-600">Subtotal</span>
          <span>{Number(project.subtotal_sale).toLocaleString()} {project.currency}</span>
        </div>
        {Number(project.discount_amount) > 0 && (
          <div className="flex justify-between py-1 text-red-700">
            <span>Descuento ({Number(project.discount_pct).toFixed(2)}%)</span>
            <span>-{Number(project.discount_amount).toLocaleString()} {project.currency}</span>
          </div>
        )}
        <div className="flex justify-between py-1">
          <span className="text-gray-600">IVA</span>
          <span>{Number(project.tax_total).toLocaleString()} {project.currency}</span>
        </div>
        <div className="mt-2 flex justify-between border-t border-gray-300 py-2 text-lg font-bold text-brand">
          <span>TOTAL</span>
          <span>{Number(project.grand_total).toLocaleString()} {project.currency}</span>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          Margen: {Number(project.margin_pct).toFixed(2)}% · Costo: {Number(project.subtotal_cost).toLocaleString()}
        </div>
      </div>
    </div>
  );
}
