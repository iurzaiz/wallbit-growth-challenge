"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { API_URL, trackEvent } from "../api";

type FundingMethod = {
  id: string;
  name: string;
  kind: string;
  currency: string;
  settlement_hours: number;
  fee_pct: string;
};

type FundingScreen = {
  country: string;
  variant: "A" | "B";
  assigned_at: string;
  recommended_method_id: string | null;
  methods: FundingMethod[];
};

// Deterministic (seeded by method + user), not random — same selection
// always shows the same mock data instead of reshuffling on every re-render.
function mockAccountDetails(method: FundingMethod, seed: string): Record<string, string> {
  const at = (i: number) => seed.charCodeAt(i % seed.length);
  const digits = (n: number) =>
    Array.from({ length: n }, (_, i) => (at(i) + i) % 10).join("");
  const hex = (n: number) =>
    Array.from({ length: n }, (_, i) => "0123456789abcdef"[(at(i) + i) % 16]).join("");

  switch (method.kind) {
    case "local_transfer":
      return {
        Banco: "Wallbit S.A.",
        Titular: "Wallbit Payments Ltd",
        "Número de cuenta": `${digits(4)}-${digits(6)}`,
        Referencia: `WB-${digits(8)}`,
      };
    case "bank_transfer":
      return {
        Banco: "Wallbit Bank N.A.",
        Titular: "Wallbit Payments Ltd",
        SWIFT: "WLBTUS33",
        "Cuenta / IBAN": `${digits(2)} ${digits(4)} ${digits(4)} ${digits(4)}`,
      };
    case "crypto":
      return {
        Red: method.name,
        Dirección: `0x${hex(40)}`,
      };
    case "third_party":
      return {
        Cuenta: `wallbit-${digits(6)}@${method.id}.pay`,
        Referencia: `WB-${digits(8)}`,
      };
    default:
      return {};
  }
}

// The backend's validation messages are in English (that's fine — it's an
// API). We only translate the ones we know about for display here.
const ERROR_TRANSLATIONS: Record<string, string> = {
  "User not found.": "El usuario no existe.",
  "This field may not be null.": "Falta el user_id.",
};

// DRF validation errors look like {"user_id": ["User not found."]} — flatten
// whatever fields/messages come back into one readable sentence instead of
// showing the raw JSON.
function extractErrorMessage(body: unknown): string {
  if (body && typeof body === "object") {
    const messages = Object.values(body as Record<string, unknown>)
      .flat()
      .filter((m): m is string => typeof m === "string")
      .map((m) => ERROR_TRANSLATIONS[m] ?? m);
    if (messages.length) return messages.join(" ");
  }
  return "Ocurrió un error inesperado.";
}

function MethodRow({ method, onSelect }: { method: FundingMethod; onSelect: () => void }) {
  return (
    <div className="card">
      <div>
        <strong>{method.name}</strong>
        <div style={{ fontSize: "0.85rem" }}>
          {method.currency} — liquida en {method.settlement_hours}h — fee {method.fee_pct}%
        </div>
      </div>
      <button className="btn secondary" onClick={onSelect}>
        Elegir
      </button>
    </div>
  );
}

function AccountDetails({ method, userId }: { method: FundingMethod; userId: string }) {
  const details = mockAccountDetails(method, `${method.id}-${userId}`);

  return (
    <div className="card" style={{ flexDirection: "column", alignItems: "stretch", gap: "0.6rem" }}>
      {Object.entries(details).map(([label, value]) => (
        <div key={label} style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
          <span style={{ fontSize: "0.85rem" }}>{label}</span>
          <strong style={{ color: "var(--foreground)", fontFamily: "var(--font-geist-mono)" }}>{value}</strong>
        </div>
      ))}
    </div>
  );
}

function FundingScreenInner() {
  const userId = useSearchParams().get("user_id");

  const [screen, setScreen] = useState<FundingScreen | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showOthers, setShowOthers] = useState(false);
  const [selected, setSelected] = useState<FundingMethod | null>(null);

  useEffect(() => {
    if (!userId) return;
    fetch(`${API_URL}/funding-screen?user_id=${encodeURIComponent(userId)}`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(extractErrorMessage(body));
        return body as FundingScreen;
      })
      .then(setScreen)
      .catch((err) => setError(String(err.message)));
  }, [userId]);

  if (!userId) return <p>Falta ?user_id= en la URL.</p>;
  if (error) {
    return (
      <>
        <h1>No pudimos mostrar esta pantalla</h1>
        <p>{error}</p>
        <Link href="/" className="btn secondary">
          Volver
        </Link>
      </>
    );
  }
  if (!screen) return <p>Cargando...</p>;

  const recommended = screen.methods.find((m) => m.id === screen.recommended_method_id);
  const others = screen.methods.filter((m) => m.id !== screen.recommended_method_id);

  function selectMethod(method: FundingMethod) {
    setSelected(method);
    trackEvent(userId!, "method_selected", { method_id: method.id });
  }

  function expandOthers() {
    setShowOthers(true);
    trackEvent(userId!, "other_methods_expanded");
  }

  return (
    <>
      <h1>Ingresar dinero</h1>
      <p>
        Usuario: {userId} — País: {screen.country} — Variante: <span className="badge">{screen.variant}</span>
      </p>

      {selected ? (
        <>
          <h2>Transferí usando estos datos</h2>
          <p>
            Elegiste <strong style={{ color: "var(--foreground)" }}>{selected.name}</strong>.
          </p>
          <AccountDetails method={selected} userId={userId} />
        </>
      ) : screen.variant === "B" && recommended ? (
        <>
          <h2>Método recomendado para vos</h2>
          <MethodRow method={recommended} onSelect={() => selectMethod(recommended)} />

          {!showOthers ? (
            <button className="btn secondary" onClick={expandOthers}>
              Ver otras opciones
            </button>
          ) : (
            <>
              <h2>Otras opciones</h2>
              {others.map((m) => (
                <MethodRow key={m.id} method={m} onSelect={() => selectMethod(m)} />
              ))}
            </>
          )}
        </>
      ) : (
        <>
          <h2>Elegí un método</h2>
          {screen.methods.map((m) => (
            <MethodRow key={m.id} method={m} onSelect={() => selectMethod(m)} />
          ))}
        </>
      )}
    </>
  );
}

export default function FundingScreenPage() {
  return (
    <Suspense fallback={<p>Cargando...</p>}>
      <FundingScreenInner />
    </Suspense>
  );
}
