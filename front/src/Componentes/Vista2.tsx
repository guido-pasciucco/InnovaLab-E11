import type { ConsultationRequest, ConsultationResponse } from "../types";

interface Vista2Props {
  actividad: string;
  direccion: string;
  onVerResultados: (datos: ConsultationRequest) => void;
  onCancelar: () => void;
  busy: boolean;
  result: ConsultationResponse | null;
}

export default function Vista2({
  actividad,
  direccion,
  onVerResultados,
  onCancelar,
  busy,
  result,
}: Vista2Props) {
  const handleVerResultados = () => {
    onVerResultados({
      activity: actividad,
      address: direccion,
    });
  };

  const handleCancelar = () => {
    onCancelar();
  };

  return (
    <section>
      <h1>Consulta inteligente</h1>

      <p>
        <strong>Actividad:</strong> {actividad}
      </p>

      <p>
        <strong>Dirección:</strong> {direccion}
      </p>

      <button
        type="button"
        onClick={handleVerResultados}
        disabled={busy}
      >
        {busy ? "Procesando..." : "Ver resultados"}
      </button>

      <button type="button" onClick={handleCancelar}>
        Cancelar
      </button>

      {result && (
        <section aria-live="polite">
          <h2>Resultados de la consulta</h2>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </section>
      )}
    </section>
  );
}
