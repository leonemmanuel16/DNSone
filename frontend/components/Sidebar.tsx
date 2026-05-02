"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearAuth, getUser } from "@/lib/auth";

const NAV = [
  { href: "/projects", label: "Cotizaciones", icon: "📋" },
  { href: "/products", label: "Productos", icon: "📦" },
  { href: "/customers", label: "Clientes", icon: "🏢" },
  { href: "/settings", label: "Configuración", icon: "⚙️" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const user = getUser();

  function logout() {
    clearAuth();
    router.push("/login");
  }

  return (
    <aside className="flex w-60 flex-col border-r border-gray-200 bg-white">
      <div className="border-b border-gray-200 px-6 py-5">
        <div className="text-xl font-bold text-brand">DNS One</div>
        <div className="text-xs text-gray-500">CRM + ERP</div>
      </div>

      <nav className="flex-1 px-3 py-4">
        {NAV.map((it) => {
          const active = pathname?.startsWith(it.href);
          return (
            <Link
              key={it.href}
              href={it.href}
              className={`mb-1 flex items-center gap-3 rounded px-3 py-2 text-sm transition ${
                active
                  ? "bg-brand text-white"
                  : "text-gray-700 hover:bg-gray-100"
              }`}
            >
              <span>{it.icon}</span>
              <span>{it.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-gray-200 p-4">
        {user && (
          <div className="mb-2 text-xs">
            <div className="font-medium text-gray-800">{user.full_name}</div>
            <div className="text-gray-500">{user.email}</div>
            {user.role && (
              <div className="mt-1 inline-block rounded bg-gray-100 px-2 py-0.5 text-[10px] uppercase text-gray-600">
                {user.role.name}
              </div>
            )}
          </div>
        )}
        <button
          onClick={logout}
          className="w-full rounded border border-gray-300 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
        >
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
