import { useMemo, useState, type FormEvent } from "react";
import QueryForm from "./Componentes/QueryForm";
import MapPanel from "./Componentes/MapPanel";
import SourceList from "./Componentes/SourceList";
import { submitConsultation, submitFollowUp } from "./api/client";
import type { ConsultationRequest, ConsultationResponse } from "./types";

type Step = 1 | 2 | 3 | 4 | 5;
const steps = ["Consulta", "Análisis", "Orientación", "Mapa", "Asistente"];

export default function App() {
  const [step, setStep] = useState<Step>(1);
  const [query, setQuery] = useState<ConsultationRequest>({ activity: "", address: "" });
  const [result, setResult] = useState<ConsultationResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [checked, setChecked] = useState<string[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [assistantBusy, setAssistantBusy] = useState(false);

  const progress = useMemo(() => result?.steps.length
    ? Math.round((checked.length / result.steps.length) * 100) : 0, [checked, result]);

  async function handleSubmit(data: ConsultationRequest) {
    setQuery(data);
    setResult(null);
    setChecked([]);
    setAnswer("");
    setError("");
    setStep(2);
    setBusy(true);
    try {
      const response = await submitConsultation(data);
      setResult(response);
      setStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No pudimos procesar la consulta. Intentá nuevamente.");
      setStep(1);
    } finally {
      setBusy(false);
    }
  }

  function startOver() {
    setStep(1);
    setQuery({ activity: "", address: "" });
    setResult(null);
    setChecked([]);
    setQuestion("");
    setAnswer("");
    setError("");
  }

  async function askAssistant(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!result || !question.trim() || assistantBusy) return;
    setAssistantBusy(true);
    setAnswer("");
    try {
      const response = await submitFollowUp(result.consultationId, { question: question.trim() });
      setAnswer(response.answer);
    } catch (err) {
      setAnswer(err instanceof Error ? err.message : "No se pudo enviar la pregunta.");
    } finally {
      setAssistantBusy(false);
    }
  }

  const queryBar = step >= 3 && (
    <div className="query-bar">
      <div className="query-bar__summary">
        <span className="query-bar__label">Tu consulta</span>
        <span className="query-pill">{query.activity}</span>
        <span className="query-pill">{query.address}</span>
        <button className="text-button" onClick={() => setStep(1)} type="button">Editar consulta</button>
      </div>
      <nav className="tabs" aria-label="Secciones de la consulta">
        <button className={step === 3 ? "is-active" : ""} onClick={() => setStep(3)} type="button">Orientación</button>
        <button className={step === 4 ? "is-active" : ""} onClick={() => setStep(4)} type="button">Mapa</button>
        <button className={step === 5 ? "is-active" : ""} onClick={() => setStep(5)} type="button">Asistente</button>
      </nav>
    </div>
  );

  return (
    <div className="app">
      <header className="topbar">
        <button className="brand" type="button" onClick={startOver} aria-label="Volver al inicio de Conco">
          <img className="brand-logo" src="/conco-logo.png" alt="Conco" />
        </button>
        <div className="topbar-caption"><span className="caption-dot" />Orientación inteligente para emprender</div>
      </header>

      <nav className="steps" aria-label="Pasos de la consulta">
        {steps.map((label, index) => {
          const number = index + 1;
          const completed = number < step;
          return (
            <div className={`step ${number === step ? "active" : ""} ${completed ? "completed" : ""}`} key={label}
              aria-current={number === step ? "step" : undefined}>
              <span className="step-number">{completed ? "✓" : number}</span>
              <span>{label}</span>
            </div>
          );
        })}
      </nav>

      {queryBar}

      <main className={`main-content ${step >= 3 ? "main-content--wide" : ""}`}>
        {step === 1 && (
          <section className="hero">
            <p className="eyebrow">TU ACTIVIDAD · TU DIRECCIÓN · TU PRÓXIMO PASO</p>
            <h1>Contanos qué querés hacer <span>y dónde.</span></h1>
            <p className="hero-description">Indicá la actividad y la dirección. Conco organiza la información disponible para orientarte sobre los próximos pasos de tu emprendimiento.</p>
            <div className="section-heading">
              <span className="section-icon">01</span>
              <div><h2>Empecemos por tu idea</h2><p>Completá los datos para iniciar tu consulta.</p></div>
            </div>
            <QueryForm busy={busy} onSubmit={handleSubmit} />
            {error && <p className="error-message" role="alert">{error}</p>}
            <p className="security-note"><span className="security-dot" />Tus datos se utilizan para preparar esta consulta.</p>
          </section>
        )}

        {step === 2 && (
          <section className="analysis-page panel" aria-live="polite">
            <p className="eyebrow">PASO 2 · ANÁLISIS</p>
            <h1>{busy ? "Estamos interpretando tu consulta" : "Consulta procesada"}</h1>
            <p className="results-intro">Identificamos la actividad y la ubicación para preparar una orientación con los datos disponibles.</p>
            <div className="analysis-summary">
              <article><span>ACTIVIDAD</span><strong>{query.activity}</strong></article>
              <article><span>UBICACIÓN</span><strong>{query.address}</strong></article>
            </div>
            <div className="loading-line"><span /></div>
            <p className="analysis-status">{busy ? "Consultando la información disponible…" : "Preparando resultados…"}</p>
            <button className="secondary" type="button" onClick={() => setStep(1)} disabled={busy}>Volver a editar</button>
          </section>
        )}

        {step === 3 && result && (
          <div className="orientation-layout">
            <section className="content-column">
              <div className="page-heading">
                <p className="eyebrow">PASO 3 · ORIENTACIÓN</p>
                <h1>Trámites relacionados</h1>
                <p>Una guía inicial de temas que conviene revisar para avanzar con tu actividad.</p>
              </div>
              <div className="guidance-list">
                {result.steps.length ? result.steps.map((item, index) => (
                  <article className="guidance-card" key={item.id}>
                    <div className="guidance-card__top">
                      <span className="guidance-number">{String(index + 1).padStart(2, "0")}</span>
                      <span className="guidance-tag">PASO A REVISAR</span>
                    </div>
                    <h2>{item.title}</h2>
                    <p>{item.description}</p>
                    {item.documents?.length ? <div className="document-list"><strong>Podés necesitar:</strong>{item.documents.map(doc => <span key={doc}>• {doc}</span>)}</div> : null}
                    <label className="review-check">
                      <input type="checkbox" checked={checked.includes(item.id)}
                        onChange={e => setChecked(old => e.target.checked ? [...old, item.id] : old.filter(id => id !== item.id))} />
                      <span>Marcar como revisado</span>
                    </label>
                  </article>
                )) : <article className="guidance-card"><h2>Orientación en preparación</h2><p>{result.summary}</p></article>}
              </div>
              <div className="progress-panel">
                <div><strong>Tu avance</strong><span>{checked.length} de {result.steps.length} revisados</span></div>
                <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
              </div>
              <div className="orientation-actions">
                <button className="secondary" type="button" onClick={() => setStep(2)}>← Volver al análisis</button>
                <button className="primary" type="button" onClick={() => setStep(4)}>Ver mapa →</button>
              </div>
            </section>
            <aside className="side-column">
              <section className="panel understood-card">
                <h2>Lo que entendimos</h2>
                <div className="result-detail"><span>Actividad</span><p>{result.interpretedActivity}</p></div>
                <div className="result-detail"><span>Ubicación</span><p>{result.normalizedAddress}</p></div>
                <p className="small-note">{result.summary}</p>
              </section>
              <SourceList sources={result.sources} />
              {result.limitations.length > 0 && <div className="notice"><span className="notice-icon">i</span><div><strong>Tené en cuenta</strong><p>{result.limitations.join(" ")}</p></div></div>}
            </aside>
          </div>
        )}

        {step === 4 && result && (
          <div className="map-page">
            <div className="page-heading">
              <p className="eyebrow">PASO 4 · MAPA</p>
              <h1>Explorá la ubicación</h1>
              <p>Visualizá el punto asociado a tu consulta y las capas territoriales disponibles.</p>
            </div>
            <MapPanel point={result.point} address={result.normalizedAddress} features={result.territorialFeatures} />
            <div className="orientation-actions">
              <button className="secondary" type="button" onClick={() => setStep(3)}>← Volver a orientación</button>
              <button className="primary" type="button" onClick={() => setStep(5)}>Consultar al asistente →</button>
            </div>
          </div>
        )}

        {step === 5 && result && (
          <section className="assistant-page">
            <div className="page-heading">
              <p className="eyebrow">PASO 5 · ASISTENTE</p>
              <h1>¿Qué necesitás aclarar?</h1>
              <p>Hacé una pregunta sobre la orientación de tu consulta.</p>
            </div>
            <div className="assistant-card panel">
              <div className="assistant-intro"><span className="assistant-avatar">C</span><div><strong>Asistente Conco</strong><span>Ayuda contextual sobre tu consulta</span></div></div>
              <div className="assistant-message"><p>Hola. Puedo ayudarte a revisar la información de esta consulta. ¿Qué te gustaría saber?</p></div>
              <form className="assistant-form" onSubmit={askAssistant}>
                <label htmlFor="assistant-question">Tu pregunta</label>
                <textarea id="assistant-question" value={question} onChange={e => setQuestion(e.target.value)}
                  placeholder="Ej.: ¿Qué documentación debería revisar primero?" rows={3} required />
                <button className="primary" type="submit" disabled={assistantBusy || !question.trim()}>{assistantBusy ? "Enviando…" : "Enviar pregunta →"}</button>
              </form>
              {answer && <div className="assistant-answer" aria-live="polite"><strong>Respuesta</strong><p>{answer}</p><small>Respuesta de demostración: verificá siempre los requisitos en las fuentes oficiales.</small></div>}
              <p className="small-note">La respuesta depende de las integraciones disponibles. No reemplaza la consulta ante organismos oficiales.</p>
            </div>
            <div className="orientation-actions"><button className="secondary" type="button" onClick={() => setStep(4)}>← Volver al mapa</button><button className="primary" type="button" onClick={startOver}>Nueva consulta →</button></div>
          </section>
        )}
      </main>

      <footer className="footer">
        <img src="/conco-logo.png" alt="Conco" className="footer-logo" />
        <p>Orientación inicial para emprendedores</p><span>Tu idea, un próximo paso.</span>
      </footer>
    </div>
  );
}
