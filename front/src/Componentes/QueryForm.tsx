import { useState, type FormEvent } from "react";
import type { ConsultationRequest } from "../types";

type Props = { onSubmit: (value: ConsultationRequest) => void; busy: boolean };
const examples = [
  { label: "Cafetería", activity: "Abrir una cafetería", address: "Av. Cabildo 2040, Belgrano" },
  { label: "Almacén", activity: "Abrir un almacén", address: "Av. Rivadavia 5200, Caballito" },
  { label: "Peluquería", activity: "Abrir una peluquería", address: "Av. Santa Fe 1800, Recoleta" },
];

export default function QueryForm({ onSubmit, busy }: Props) {
  const [activity, setActivity] = useState("");
  const [address, setAddress] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activity.trim() || !address.trim()) {
      setError("Completá la actividad y la dirección para continuar.");
      return;
    }
    setError("");
    onSubmit({ activity: activity.trim(), address: address.trim() });
  }

  return (
    <form className="query-form panel" onSubmit={handleSubmit} noValidate>
      <div className="query-field">
        <label htmlFor="activity">¿Qué actividad querés realizar?</label>
        <input id="activity" name="activity" value={activity} onChange={e => { setActivity(e.target.value); setError(""); }}
          placeholder="Ej.: abrir una cafetería" maxLength={300} autoComplete="off" aria-invalid={!!error && !activity.trim()} />
      </div>
      <div className="query-field">
        <label htmlFor="address">¿En qué dirección?</label>
        <input id="address" name="address" value={address} onChange={e => { setAddress(e.target.value); setError(""); }}
          placeholder="Calle, altura y barrio" maxLength={300} autoComplete="street-address" aria-invalid={!!error && !address.trim()} />
        <span className="field-hint">Ingresá calle y altura, o una referencia de ubicación.</span>
      </div>
      {error && <p className="error-message" role="alert">{error}</p>}
      <button className="primary query-submit" type="submit" disabled={busy}>{busy ? "Consultando…" : <>Consultar requisitos <span aria-hidden="true">→</span></>}</button>
      <div className="examples"><span className="examples-title">Probá con un ejemplo</span><div className="example-chips">
        {examples.map(item => <button key={item.label} type="button" className="chip" onClick={() => { setActivity(item.activity); setAddress(item.address); setError(""); }}>{item.label}</button>)}
      </div></div>
      <p className="hint">La orientación es inicial y depende de las fuentes oficiales conectadas.</p>
    </form>
  );
}
