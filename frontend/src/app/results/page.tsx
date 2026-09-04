"use client";

import { useEffect, useState } from "react";
import { API_URL } from "../api";

type VariantResult = {
  variant: string;
  assigned: number;
  converted: number;
  conversion_rate: number;
};

export default function ResultsPage() {
  const [results, setResults] = useState<VariantResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/experiment/results`)
      .then((res) => {
        if (!res.ok) throw new Error(`El servidor respondió ${res.status}.`);
        return res.json();
      })
      .then(setResults)
      .catch(() => setError("No pudimos conectar con el backend. ¿Está corriendo en localhost:8000?"));
  }, []);

  if (error) return <p>{error}</p>;
  if (!results) return <p>Cargando...</p>;

  return (
    <>
      <h1>Resultado del experimento</h1>
      <p>¿Cuál de las dos variantes convierte mejor?</p>

      <table style={{ marginTop: "1.5rem" }}>
        <thead>
          <tr>
            <th>Variante</th>
            <th>Asignados</th>
            <th>Convertidos</th>
            <th>Tasa</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => (
            <tr key={r.variant}>
              <td>
                <span className="badge">{r.variant}</span>
              </td>
              <td>{r.assigned}</td>
              <td>{r.converted}</td>
              <td>{(r.conversion_rate * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
