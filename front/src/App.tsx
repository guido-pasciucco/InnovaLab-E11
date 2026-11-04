import { useState } from "react";
import Vista2 from "./Componentes/Vista2";
import type {
  ConsultationRequest,
  ConsultationResponse,
} from "./types";

export default function App() {
  const actividad = "Casa de comidas";
  const direccion = "Av. Rivadavia 1234, CABA";

  const [consultaEnviada, setConsultaEnviada] = useState(false);

  const [datosConsulta, setDatosConsulta] =
    useState<ConsultationRequest | null>(null);

  const [resultado, setResultado] =
    useState<ConsultationResponse | null>(null);

  const handleVerResultados = (datos: ConsultationRequest) => {
    console.log("Consulta recibida:", datos);

    setDatosConsulta(datos);
    setConsultaEnviada(true);

    // La consulta a fuentes externas todavía no está implementada.
    setResultado(null);
  };

  const handleCancelar = () => {
    console.log("Consulta cancelada");

    setConsultaEnviada(false);
    setDatosConsulta(null);
    setResultado(null);
  };

  return (
    <>
      <Vista2
        actividad={actividad}
        direccion={direccion}
        onVerResultados={handleVerResultados}
        onCancelar={handleCancelar}
        busy={false}
        result={resultado}
      />

      {consultaEnviada && datosConsulta && (
        <section
          role="status"
          style={{
            maxWidth: "800px",
            margin: "24px auto",
            padding: "20px",
            border: "1px solid #0b6485",
            borderRadius: "8px",
            background: "#f0f9ff",
            color: "#17324d",
          }}
        >
          <h2>Consulta recibida correctamente</h2>

          <p>
            <strong>Actividad:</strong> {datosConsulta.activity}
          </p>

          <p>
            <strong>Dirección:</strong> {datosConsulta.address}
          </p>

          <p>
            Los datos fueron recibidos por la aplicación. La consulta a
            fuentes externas todavía no está implementada.
          </p>
        </section>
      )}
    </>
  );
}
