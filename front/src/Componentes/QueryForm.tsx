import { useState, type FormEvent } from "react";
import AddressAutocomplete from "./AddressAutocomplete";
import type { Address, ConsultationRequest, GeoPoint } from "../types";

type Props = { onSubmit: (value: ConsultationRequest) => void; busy: boolean };
// Georef works best without the neighbourhood, so the examples only carry street and number.
const examples = [
  { label: "Cafetería", activity: "Abrir una cafetería", address: "Av. Cabildo 2040" },
  { label: "Almacén", activity: "Abrir un almacén", address: "Av. Rivadavia 5200" },
  { label: "Peluquería", activity: "Abrir una peluquería", address: "Av. Santa Fe 1800" },
];

function toGeoPoint(coordinates: Address["coordinates"]): GeoPoint | null {
  return coordinates ? { lat: coordinates.latitude, lng: coordinates.longitude } : null;
}

export default function QueryForm({ onSubmit, busy }: Props) {
  const [activity, setActivity] = useState("");
  const [address, setAddress] = useState("");
  const [selectedAddress, setSelectedAddress] = useState<Address | null>(null);
  const [searchAvailable, setSearchAvailable] = useState(true);
  const [error, setError] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activity.trim() || !address.trim()) {
      setError("Completá la actividad y la dirección para continuar.");
      return;
    }
    if (selectedAddress) {
      setError("");
      onSubmit({ activity: activity.trim(), address: selectedAddress.full_address, point: toGeoPoint(selectedAddress.coordinates) });
      return;
    }
    if (searchAvailable) {
      setError("Elegí una dirección de la lista de sugerencias.");
      return;
    }
    setError("");
    onSubmit({ activity: activity.trim(), address: address.trim(), point: null });
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
        <AddressAutocomplete id="address" value={address} selected={selectedAddress}
          invalid={!!error && !selectedAddress && (!address.trim() || searchAvailable)}
          onChange={value => { setAddress(value); setError(""); }} onSelect={setSelectedAddress}
          onAvailabilityChange={setSearchAvailable} />
        <span className="field-hint">Escribí calle y altura, sin el barrio, y elegí una opción de la lista. También podés usar «Corrientes y Callao» o «Corrientes entre Callao y Riobamba».</span>
      </div>
      {error && <p className="error-message" role="alert">{error}</p>}
      <button className="primary query-submit" type="submit" disabled={busy}>{busy ? "Consultando…" : <>Consultar requisitos <span aria-hidden="true">→</span></>}</button>
      <div className="examples"><span className="examples-title">Probá con un ejemplo</span><div className="example-chips">
        {examples.map(item => <button key={item.label} type="button" className="chip" onClick={() => { setActivity(item.activity); setAddress(item.address); setSelectedAddress(null); setError(""); }}>{item.label}</button>)}
      </div></div>
      <p className="hint">La orientación es inicial y depende de las fuentes oficiales conectadas.</p>
    </form>
  );
}
