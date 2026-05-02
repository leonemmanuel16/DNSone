"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiProjects, ApiError } from "@/lib/api";
import type { Project } from "@/lib/types";

const STATUS_LABEL: Record<string, string> = {
  draft: "Borrador",
  sent: "Enviada",
  approved: "Aprobada",
  rejected: "Rechazada",
  converted: "Convertida",
  cancelled: "Cancelada",
};

const STATUS_COLOR: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  sent: "bg-blue-100 text-blue-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  converted: "bg-purple-100 text-purple-700",
  cancelled: "bg-gray-200 text-gray-500",
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiProjects
      .list()
      .then((p) => setProjects(p.items))
      .catch((e) => setError(e instanceof ApiError ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cotizaciones</h1>
          <p className="text-sm text-gray-500">Cada cotización es un proyecto</p>
        </div>
        <Link
          href="/projects/new"
          className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-light"
        >
          + Nueva cotización
        </Link>
      </div>

      {error && <div className="mb-4 rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <div className="overflow-x-auto rounded border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase text-gray-600">
            <tr>
              <th className="px-4 py-2">Folio</th>
              <th className="px-4 py-2">Nombre</th>
              <th className="px-4 py-2">Cliente</th>
              <th className="px-4 py-2">Estatus</th>
              <th className="px-4 py-2 text-right">Total</th>
              <th className="px-4 py-2">Folio BIND</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="p-6 text-center text-gray-500">Cargando...</td></tr>
            ) : projects.length === 0 ? (
              <tr><td colSpan={6} className="p-6 text-center text-gray-500">Sin cotizaciones aún</td></tr>
            ) : projects.map((p) => (
              <tr key={p.id} className="cursor-pointer border-t border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-2">
                  <Link href={`/projects/${p.id}`} className="font-mono text-brand hover:underline">
                    {p.code}
                  </Link>
                </td>
                <td className="px-4 py-2">{p.name}</td>
                <td className="px-4 py-2">{p.customer?.name || "—"}</td>
                <td className="px-4 py-2">
                  <span className={`rounded px-2 py-0.5 text-xs ${STATUS_COLOR[p.status]}`}>
                    {STATUS_LABEL[p.status] || p.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-right font-medium">
                  {Number(p.grand_total).toLocaleString("en-US", { minimumFractionDigits: 2 })} {p.currency}
                </td>
                <td className="px-4 py-2 text-xs">
                  {p.bind_folio ? <span className="text-brand-accent font-mono">{p.bind_folio}</span> : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
