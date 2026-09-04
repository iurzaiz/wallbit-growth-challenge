"use client";

import { useState } from "react";
import Link from "next/link";

export default function Home() {
  const [userId, setUserId] = useState("");

  return (
    <>
      <h1>Experimento de pantalla de fondeo</h1>
      <p>
        No hay login: escribí un user_id o elegí uno de la lista para ver su pantalla de fondeo.
      </p>

      <form
        style={{ display: "flex", gap: "0.5rem", margin: "1.5rem 0" }}
        onSubmit={(e) => {
          e.preventDefault();
          window.location.href = `/funding-screen?user_id=${encodeURIComponent(userId)}`;
        }}
      >
        <input value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="usr_000001" />
        <button type="submit" className="btn">
          Ir a la pantalla de fondeo
        </button>
      </form>

      <div style={{ display: "flex", gap: "0.75rem" }}>
        <Link href="/users" className="btn secondary">
          Ver usuarios
        </Link>
        <Link href="/results" className="btn secondary">
          Ver resultado del experimento
        </Link>
      </div>
    </>
  );
}
