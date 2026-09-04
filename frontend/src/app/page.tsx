"use client";

import { useState } from "react";

export default function Home() {
  const [userId, setUserId] = useState("");

  return (
    <>
      <h1>Growth challenge</h1>
      <p>No hay login: escribí un user_id de data/users.json (ej. usr_000001) para ver su pantalla de fondeo.</p>

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

      <a href="/results" className="btn secondary">
        Ver resultado del experimento
      </a>
    </>
  );
}
