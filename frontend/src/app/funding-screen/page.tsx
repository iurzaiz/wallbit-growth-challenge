"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
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

function FundingScreenInner() {
  const userId = useSearchParams().get("user_id");

  const [screen, setScreen] = useState<FundingScreen | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showOthers, setShowOthers] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) return;
    fetch(`${API_URL}/funding-screen?user_id=${encodeURIComponent(userId)}`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(JSON.stringify(body));
        return body as FundingScreen;
      })
      .then(setScreen)
      .catch((err) => setError(String(err.message)));
  }, [userId]);

  if (!userId) return <p>Falta ?user_id= en la URL.</p>;
  if (error) return <p>Error: {error}</p>;
  if (!screen) return <p>Cargando...</p>;

  const recommended = screen.methods.find((m) => m.id === screen.recommended_method_id);
  const others = screen.methods.filter((m) => m.id !== screen.recommended_method_id);

  function selectMethod(method: FundingMethod) {
    setSelected(method.id);
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
          <h2>Listo</h2>
          <p>
            Elegiste <strong style={{ color: "var(--foreground)" }}>{selected}</strong>. (acá irían los datos de
            la cuenta para transferir)
          </p>
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
