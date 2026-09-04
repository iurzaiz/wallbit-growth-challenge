"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { API_URL } from "../api";

type UserRow = {
  id: string;
  country: string;
  kyc_status: string;
  created_at: string;
};

type UsersResponse = {
  count: number;
  next: string | null;
  previous: string | null;
  results: UserRow[];
};

export default function UsersPage() {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<UsersResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setError(null);
    const params = new URLSearchParams({ page: String(page) });
    if (query.trim()) params.set("q", query.trim());
    fetch(`${API_URL}/users?${params}`)
      .then((res) => {
        if (!res.ok) throw new Error(`El servidor respondió ${res.status}.`);
        return res.json();
      })
      .then(setData)
      .catch(() => setError("No pudimos conectar con el backend. ¿Está corriendo en localhost:8000?"));
  }, [query, page]);

  if (error) {
    return (
      <>
        <h1>Usuarios</h1>
        <p>{error}</p>
      </>
    );
  }

  return (
    <>
      <h1>Usuarios</h1>
      <p>
        {data ? `${data.count} usuarios` : "Cargando..."} de <code>data/users.json</code>. Elegí uno para ver su
        pantalla de fondeo.
      </p>

      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setPage(1);
        }}
        placeholder="Buscar por id o país (ej. AR)"
        style={{ width: "100%", marginTop: "1rem" }}
      />

      {!data ? (
        <p style={{ marginTop: "1rem" }}>Cargando...</p>
      ) : data.results.length === 0 ? (
        <p style={{ marginTop: "1rem" }}>Sin resultados.</p>
      ) : (
        data.results.map((u) => (
          <div key={u.id} className="card">
            <div>
              <strong style={{ fontFamily: "var(--font-geist-mono)" }}>{u.id}</strong>
              <div style={{ fontSize: "0.85rem" }}>
                País: {u.country} — KYC: {u.kyc_status}
              </div>
            </div>
            <Link href={`/funding-screen?user_id=${u.id}`} className="btn secondary">
              Ver pantalla
            </Link>
          </div>
        ))
      )}

      {data && (data.next || data.previous) && (
        <div style={{ display: "flex", gap: "0.75rem", marginTop: "1rem", alignItems: "center" }}>
          <button className="btn secondary" disabled={!data.previous} onClick={() => setPage((p) => p - 1)}>
            Anterior
          </button>
          <span style={{ fontSize: "0.85rem" }}>Página {page}</span>
          <button className="btn secondary" disabled={!data.next} onClick={() => setPage((p) => p + 1)}>
            Siguiente
          </button>
        </div>
      )}
    </>
  );
}
