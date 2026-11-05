import type {
  ConsultationRequest,
  ConsultationResponse,
} from "../types";

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

  return (
    <main className="vista-consulta">
      <h1>Revisá tu consulta</h1>

      <p>
        Identificamos la actividad y la ubicación para preparar una
        orientación basada en los datos disponibles.
      </p>

      <div className="consulta-resumen">
        <h2>Lo que entendimos</h2>

        <section>
          <strong>Actividad</strong>
          <p>{actividad}</p>
        </section>

        <section>
          <strong>Ubicación</strong>
          <p>{direccion}</p>
        </section>
      </div>

      <div className="consulta-acciones">
        <button
          type="button"
          onClick={onCancelar}
          disabled={busy}
        >
          Volver
        </button>

        <button
          type="button"
          onClick={handleVerResultados}
          disabled={busy}
        >
          {busy ? "Procesando..." : "Ver resultados →"}
        </button>
      </div>

      {result && (
        <section className="resultado-resumen" aria-live="polite">
          <h2>Consulta recibida correctamente</h2>
          <p>
            Los datos fueron recibidos por la aplicación. La consulta
            a fuentes externas depende de las integraciones disponibles.
          </p>
        </section>
      )}
    </main>
  );
}