import { useState, type FormEvent } from 'react';
import type { ConsultationRequest } from '../types';

type Props = { onSubmit: (value: ConsultationRequest) => void; busy: boolean };

export default function QueryForm({ onSubmit, busy }: Props) {
  const [activity, setActivity] = useState('Abrir una cafetería');
  const [address, setAddress] = useState('Av. Corrientes 2500, CABA');

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!activity.trim() || !address.trim()) return;
    onSubmit({ activity: activity.trim(), address: address.trim() });
  }

  return <form className="query-form panel" onSubmit={handleSubmit}>
    <label htmlFor="activity">¿Qué actividad querés realizar?</label>
    <input id="activity" value={activity} onChange={e => setActivity(e.target.value)}
      placeholder="Ej.: abrir una cafetería" required />
    <label htmlFor="address">¿En qué dirección?</label>
    <input id="address" value={address} onChange={e => setAddress(e.target.value)}
      placeholder="Calle, altura y ciudad" required />
    <button className="primary" disabled={busy}>{busy ? 'Consultando fuentes…' : 'Consultar requisitos'}</button>
    <p className="hint">Demo inicial: actividad + domicilio. La respuesta real depende de fuentes oficiales conectadas.</p>
  </form>;
}
