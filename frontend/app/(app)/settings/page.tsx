"use client";

import { useEffect, useState, FormEvent } from "react";
import { apiSettings, ApiError } from "@/lib/api";
import type { BindSettings, BindSettingsUpdate, CommercialSettings } from "@/lib/types";

export default function SettingsPage() {
  const [bind, setBind] = useState<BindSettings | null>(null);
  const [commercial, setCommercial] = useState<CommercialSettings | null>(null);

  // BIND form state
  const [bindUrl, setBindUrl] = useState("");
  const [bindToken, setBindToken] = useState("");
  const [bindUseMock, setBindUseMock] = useState(true);
  const [bindTimeout, setBindTimeout] = useState(30);
  const [bindRetries, setBindRetries] = useState(3);

  // Commercial form state
  const [defaultCurrency, setDefaultCurrency] = useState<"USD" | "MXN">("USD");
  const [defaultFx, setDefaultFx] = useState("19.00");
  const [defaultTax, setDefaultTax] = useState("16.00");

  const [savingBind, setSavingBind] = useState(false);
  const [savingComm, setSavingComm] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  async function load() {
    try {
      const [b, c] = await Promise.all([apiSettings.getBind(), apiSettings.getCommercial()]);
      setBind(b);
      setBindUrl(b.bind_base_url || "");
      setBindUseMock(b.bind_use_mock);
      setBindTimeout(b.bind_timeout_seconds);
      setBindRetries(b.bind_max_retries);

      setCommercial(c);
      setDefaultCurrency(c.default_currency);
      setDefaultFx(c.default_exchange_rate_usd_mxn);
      setDefaultTax(c.default_tax_pct);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error cargando configuración");
    }
  }

  useEffect(() => { load(); }, []);

  async function saveBind(e: FormEvent) {
    e.preventDefault();
    setSavingBind(true);
    setError(null);
    setInfo(null);
    try {
      const update: BindSettingsUpdate = {
        bind_base_url: bindUrl || null,
        bind_use_mock: bindUseMock,
        bind_timeout_seconds: bindTimeout,
        bind_max_retries: bindRetries,
      };
      // Solo mandamos token si el usuario escribió algo (no pisar el guardado)
      if (bindToken !== "") {
        update.bind_api_token = bindToken;
      }
      const updated = await apiSettings.updateBind(update);
      setBind(updated);
      setBindToken(""); // limpiar input por seguridad
      setInfo("Configuración BIND guardada.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error");
    } finally {
      setSavingBind(false);
    }
  }

  async function clearToken() {
    if (!confirm("¿Borrar el token de BIND guardado?")) return;
    try {
      const updated = await apiSettings.updateBind({ bind_api_token: "" });
      setBind(updated);
      setInfo("Token eliminado.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error");
    }
  }

  async function testConnection() {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await apiSettings.testBind();
      setTestResult(
        res.ok
          ? `✅ ${res.message}${res.products_received !== undefined ? ` · ${res.products_received} productos recibidos` : ""}`
          : `❌ ${res.message}`
      );
    } catch (e) {
      setTestResult(e instanceof ApiError ? `❌ ${e.message}` : "❌ Error de red");
    } finally {
      setTesting(false);
    }
  }

  async function saveCommercial(e: FormEvent) {
    e.preventDefault();
    setSavingComm(true);
    setError(null);
    setInfo(null);
    try {
      const updated = await apiSettings.updateCommercial({
        default_currency: defaultCurrency,
        default_exchange_rate_usd_mxn: defaultFx,
        default_tax_pct: defaultTax,
      });
      setCommercial(updated);
      setInfo("Configuración comercial guardada.");
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Error");
    } finally {
      setSavingComm(false);
    }
  }

  return (
    <div className="max-w-3xl space-y-8">
      <h1 className="text-2xl font-bold text-gray-900">Configuración</h1>

      {error && <div className="rounded bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {info && <div className="rounded bg-green-50 p-3 text-sm text-green-700">{info}</div>}

      {/* ============ BIND ============ */}
      <section className="rounded border border-gray-200 bg-white p-6">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Integración Bind ERP</h2>
            <p className="text-xs text-gray-500">
              Configura la conexión al API de Bind. Cambios toman efecto sin reiniciar.
            </p>
          </div>
          {bind && (
            <span className={`rounded px-3 py-1 text-xs font-medium ${
              bind.bind_use_mock ? "bg-yellow-100 text-yellow-800" : "bg-green-100 text-green-800"
            }`}>
              {bind.bind_use_mock ? "Modo MOCK" : "Modo REAL"}
            </span>
          )}
        </div>

        <form onSubmit={saveBind} className="space-y-4">
          <div className="rounded border border-yellow-200 bg-yellow-50 p-3 text-sm text-yellow-900">
            <strong>Modo Mock:</strong> usa datos de prueba en lugar del API real. Útil para
            desarrollo. <strong>Apaga este modo solo cuando tengas URL y token reales.</strong>
          </div>

          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={bindUseMock}
              onChange={(e) => setBindUseMock(e.target.checked)}
              className="h-4 w-4"
            />
            <span className="text-sm">Usar modo mock (sin tocar API real)</span>
          </label>

          <div>
            <label className="mb-1 block text-sm font-medium">URL base del API BIND</label>
            <input
              type="url"
              value={bindUrl}
              onChange={(e) => setBindUrl(e.target.value)}
              placeholder="https://api.bind.com.mx/v1"
              className="w-full rounded border border-gray-300 px-3 py-2 font-mono text-sm"
              disabled={bindUseMock}
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Token de API</label>
            <div className="flex gap-2">
              <input
                type="password"
                value={bindToken}
                onChange={(e) => setBindToken(e.target.value)}
                placeholder={
                  bind?.bind_api_token_set
                    ? `Guardado: ${bind.bind_api_token_hint || "***"} (deja vacío para no cambiar)`
                    : "Pega aquí el token"
                }
                className="flex-1 rounded border border-gray-300 px-3 py-2 font-mono text-sm"
                disabled={bindUseMock}
                autoComplete="off"
              />
              {bind?.bind_api_token_set && (
                <button
                  type="button"
                  onClick={clearToken}
                  className="rounded border border-red-300 px-3 py-2 text-xs text-red-700 hover:bg-red-50"
                >
                  Borrar token
                </button>
              )}
            </div>
            <p className="mt-1 text-xs text-gray-500">
              El token nunca se muestra completo después de guardarlo.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">Timeout (segundos)</label>
              <input
                type="number"
                min={1}
                max={300}
                value={bindTimeout}
                onChange={(e) => setBindTimeout(Number(e.target.value))}
                className="w-full rounded border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">Reintentos máximos</label>
              <input
                type="number"
                min={0}
                max={10}
                value={bindRetries}
                onChange={(e) => setBindRetries(Number(e.target.value))}
                className="w-full rounded border border-gray-300 px-3 py-2"
              />
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={savingBind}
              className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-light disabled:opacity-60"
            >
              {savingBind ? "Guardando..." : "Guardar cambios"}
            </button>
            <button
              type="button"
              onClick={testConnection}
              disabled={testing}
              className="rounded border border-gray-300 px-4 py-2 text-sm hover:bg-gray-50 disabled:opacity-60"
            >
              {testing ? "Probando..." : "🔌 Probar conexión"}
            </button>
          </div>
          {testResult && (
            <div className="mt-2 rounded border bg-gray-50 p-3 text-sm font-mono">
              {testResult}
            </div>
          )}
        </form>
      </section>

      {/* ============ Comerciales ============ */}
      <section className="rounded border border-gray-200 bg-white p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Reglas comerciales</h2>
          <p className="text-xs text-gray-500">Valores por defecto para nuevas cotizaciones.</p>
        </div>

        <form onSubmit={saveCommercial} className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">Moneda default</label>
              <select
                value={defaultCurrency}
                onChange={(e) => setDefaultCurrency(e.target.value as "USD" | "MXN")}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="USD">USD</option>
                <option value="MXN">MXN</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">TC USD → MXN</label>
              <input
                value={defaultFx}
                onChange={(e) => setDefaultFx(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2 text-right"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">IVA default %</label>
              <input
                value={defaultTax}
                onChange={(e) => setDefaultTax(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2 text-right"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={savingComm}
            className="rounded bg-brand px-4 py-2 text-sm text-white hover:bg-brand-light disabled:opacity-60"
          >
            {savingComm ? "Guardando..." : "Guardar"}
          </button>
        </form>
      </section>
    </div>
  );
}
