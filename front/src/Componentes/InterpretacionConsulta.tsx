import { useEffect, useState, type FormEvent } from 'react';
import type { ConsultationRequest } from '../types';

type InterpretacionConsultaProps = {
  actividad: string;
  direccion: string;
  busy?: boolean;
  error?: string | null;
  onConsultar: (datos: ConsultationRequest) => void;
  onCancelar?: () => void;
};

export default function InterpretacionConsulta({
  actividad,
  direccion,
  busy = false,
  error = null,
  onConsultar,
  onCancelar,
}: InterpretacionConsultaProps) {
  // Estados de los campos editables.
  const [actividadEditada, setActividadEditada] = useState(actividad);
  const [direccionEditada, setDireccionEditada] = useState(direccion);

  // Estados de la interfaz.
  const [editarActividad, setEditarActividad] = useState(false);
  const [editarDireccion, setEditarDireccion] = useState(false);
  const [mostrarAclaracion, setMostrarAclaracion] = useState(false);

  // Estado para los mensajes de validación.
  const [errorValidacion, setErrorValidacion] = useState('');

  // Sincronizar los campos cuando cambian las propiedades del componente padre.
  useEffect(() => {
    setActividadEditada(actividad);
  }, [actividad]);

  useEffect(() => {
    setDireccionEditada(direccion);
  }, [direccion]);

  // Normalizar los valores ingresados.
  const actividadNormalizada = actividadEditada.trim();
  const direccionNormalizada = direccionEditada.trim();

  // Función principal de consulta.
  const handleConsultar = (event?: FormEvent<HTMLFormElement>) => {
    event?.preventDefault();

    // Evitar consultas con campos vacíos.
    if (!actividadNormalizada || !direccionNormalizada) {
      setErrorValidacion(
        'Por favor, completá la actividad y la dirección antes de continuar.'
      );
      return;
    }

    // Evitar envíos duplicados.
    if (busy) return;

    // Limpiar errores anteriores.
    setErrorValidacion('');

    // Preparar los datos según ConsultationRequest.
    const datos: ConsultationRequest = {
      activity: actividadNormalizada,
      address: direccionNormalizada,
    };

    // Mostrar los datos enviados en la consola del navegador.
    console.log('Datos enviados a la consulta:', datos);

    // Ejecutar la función recibida desde el componente padre.
    onConsultar(datos);
  };

  // Permitir cancelar y volver al paso anterior.
  const handleCancelar = () => {
    if (busy) return;

    if (onCancelar) {
      onCancelar();
    }
  };

  // Evitar que el formulario se envíe mediante un evento no deseado.
  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    handleConsultar(event);
  };

  return (
    <section className="interpretacion-container">
      <div className="interpretacion-content">
        {/* Encabezado */}
        <header className="interpretacion-header">
          <h1>Revisá tu consulta</h1>

          <p>
            Identificamos la actividad y la ubicación para preparar una
            orientación basada en los datos disponibles.
          </p>
        </header>

        {/* Formulario principal */}
        <form
          className="interpretacion-grid"
          onSubmit={handleSubmit}
          noValidate
        >
          {/* Columna izquierda */}
          <section className="interpretacion-card">
            <h2>Lo que entendimos</h2>

            <blockquote className="interpretacion-resumen">
              Quiero realizar la siguiente consulta:
              <strong>
                {actividadNormalizada || 'Actividad no especificada'}
              </strong>
              <span>
                en {direccionNormalizada || 'una ubicación no especificada'}.
              </span>
            </blockquote>

            {/* Actividad */}
            <article className="interpretacion-dato">
              <div className="interpretacion-dato-header">
                <span className="interpretacion-etiqueta">ACTIVIDAD</span>

                <button
                  type="button"
                  className="interpretacion-link"
                  onClick={() => {
                    setEditarActividad((actual) => !actual);
                    setErrorValidacion('');
                  }}
                  disabled={busy}
                  aria-expanded={editarActividad}
                >
                  {editarActividad ? 'Cerrar' : 'Editar'}
                </button>
              </div>

              {editarActividad ? (
                <div className="interpretacion-campo">
                  <label htmlFor="actividad-editada">
                    Describí la actividad que querés realizar
                  </label>

                  <input
                    id="actividad-editada"
                    name="activity"
                    type="text"
                    value={actividadEditada}
                    onChange={(event) => {
                      setActividadEditada(event.target.value);
                      setErrorValidacion('');
                    }}
                    placeholder="Ej.: Casa de comidas"
                    maxLength={300}
                    autoComplete="off"
                    disabled={busy}
                  />
                </div>
              ) : (
                <h3>
                  {actividadNormalizada || 'Actividad no especificada'}
                </h3>
              )}

              <p>
                Actividad declarada por el usuario. La clasificación definitiva
                dependerá de la consulta y de las fuentes oficiales disponibles.
              </p>
            </article>

            {/* Dirección */}
            <article className="interpretacion-dato">
              <div className="interpretacion-dato-header">
                <span className="interpretacion-etiqueta">UBICACIÓN</span>

                <button
                  type="button"
                  className="interpretacion-link"
                  onClick={() => {
                    setEditarDireccion((actual) => !actual);
                    setErrorValidacion('');
                  }}
                  disabled={busy}
                  aria-expanded={editarDireccion}
                >
                  {editarDireccion ? 'Cerrar' : 'Editar'}
                </button>
              </div>

              <h3>
                {direccionNormalizada || 'Dirección no especificada'}
              </h3>

              {editarDireccion && (
                <div className="interpretacion-campo">
                  <label htmlFor="direccion-editada">
                    Dirección del establecimiento
                  </label>

                  <input
                    id="direccion-editada"
                    name="address"
                    type="text"
                    value={direccionEditada}
                    onChange={(event) => {
                      setDireccionEditada(event.target.value);
                      setErrorValidacion('');
                    }}
                    placeholder="Ej.: Av. Rivadavia 1234, CABA"
                    maxLength={300}
                    autoComplete="street-address"
                    disabled={busy}
                  />
                </div>
              )}

              <p>
                La ubicación debe verificarse con los datos territoriales y las
                fuentes oficiales correspondientes.
              </p>
            </article>

            {/* Confirmación de los datos */}
            <div className="interpretacion-confirmacion">
              <label htmlFor="confirmar-correccion">
                <input
                  id="confirmar-correccion"
                  type="checkbox"
                  checked={mostrarAclaracion}
                  onChange={(event) =>
                    setMostrarAclaracion(event.target.checked)
                  }
                  disabled={busy}
                />

                <span>
                  ¿No es lo que querías decir? Podés corregir la actividad o la
                  dirección antes de continuar.
                </span>
              </label>

              {mostrarAclaracion && (
                <p className="interpretacion-ayuda">
                  Usá los botones «Editar» para corregir los datos de tu
                  consulta. Después, seleccioná «Ver resultados».
                </p>
              )}
            </div>
          </section>

          {/* Columna derecha */}
          <aside className="interpretacion-card">
            <h2>Estado de la consulta</h2>

            <p className="interpretacion-nota">
              Estas verificaciones son orientativas. Los porcentajes de
              demostración no representan el avance real de servicios externos.
            </p>

            {/* Estado de los trámites */}
            <div className="interpretacion-estados">
              <div className="interpretacion-estado">
                <div className="interpretacion-estado-header">
                  <span>Trámites y requisitos</span>
                  <span className="interpretacion-estado-texto">
                    {busy ? 'Consultando…' : 'Pendiente de consulta'}
                  </span>
                </div>

                <div
                  className="interpretacion-barra"
                  role="progressbar"
                  aria-label="Trámites y requisitos"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={busy ? 50 : 0}
                >
                  <span
                    style={{
                      width: busy ? '50%' : '0%',
                    }}
                  />
                </div>
              </div>

              <div className="interpretacion-estado">
                <div className="interpretacion-estado-header">
                  <span>Zonificación y usos del suelo</span>
                  <span className="interpretacion-estado-texto">
                    Pendiente de consulta
                  </span>
                </div>

                <div
                  className="interpretacion-barra"
                  role="progressbar"
                  aria-label="Zonificación y usos del suelo"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={0}
                >
                  <span style={{ width: '0%' }} />
                </div>
              </div>

              <div className="interpretacion-estado">
                <div className="interpretacion-estado-header">
                  <span>Habilitaciones y control</span>
                  <span className="interpretacion-estado-texto">
                    Pendiente de consulta
                  </span>
                </div>

                <div
                  className="interpretacion-barra"
                  role="progressbar"
                  aria-label="Habilitaciones y control"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={0}
                >
                  <span style={{ width: '0%' }} />
                </div>
              </div>

              <div className="interpretacion-estado">
                <div className="interpretacion-estado-header">
                  <span>Cartografía y capas territoriales</span>
                  <span className="interpretacion-estado-texto">
                    Pendiente de consulta
                  </span>
                </div>

                <div
                  className="interpretacion-barra"
                  role="progressbar"
                  aria-label="Cartografía y capas territoriales"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={0}
                >
                  <span style={{ width: '0%' }} />
                </div>
              </div>

              <div className="interpretacion-estado">
                <div className="interpretacion-estado-header">
                  <span>Datos abiertos de la ciudad</span>
                  <span className="interpretacion-estado-texto">
                    En espera
                  </span>
                </div>

                <div
                  className="interpretacion-barra"
                  role="progressbar"
                  aria-label="Datos abiertos de la ciudad"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={0}
                >
                  <span style={{ width: '0%' }} />
                </div>
              </div>
            </div>

            {/* Mensajes de error */}
            {(errorValidacion || error) && (
              <div
                className="interpretacion-error"
                role="alert"
                aria-live="assertive"
              >
                {errorValidacion || error}
              </div>
            )}

            {/* Acciones */}
            <div className="interpretacion-acciones">
              <button
                type="button"
                className="interpretacion-cancelar"
                onClick={handleCancelar}
                disabled={busy}
              >
                Cancelar
              </button>

              <button
                type="submit"
                className="interpretacion-submit"
                disabled={busy}
              >
                {busy ? (
                  <>
                    <span
                      className="interpretacion-spinner"
                      aria-hidden="true"
                    />
                    Procesando…
                  </>
                ) : (
                  <>
                    Ver resultados
                    <span aria-hidden="true"> →</span>
                  </>
                )}
              </button>
            </div>
          </aside>
        </form>
      </div>
    </section>
  );
}