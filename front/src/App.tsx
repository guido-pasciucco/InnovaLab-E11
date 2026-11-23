import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import QueryForm from "./Componentes/QueryForm";
import MapPanel from "./Componentes/MapPanel";
import RequirementsChecklist from "./Componentes/RequirementsChecklist";
import OfficialSources from "./Componentes/OfficialSources";
import ContextQuestions from "./Componentes/ContextQuestions";
import AnalysisSources from "./Componentes/AnalysisSources";
import ErrorBoundary from "./Componentes/ErrorBoundary";
import RecentSearches from "./Componentes/RecentSearches";
import { getActivityProcedures, submitConsultation, submitFollowUp } from "./api/client";
import { describeError } from "./api/errors";
import type { HistoryEntry } from "./history/searchHistory";
import { useSearchHistory } from "./history/useSearchHistory";
import { HOME_PATH, STEPS, isStepAvailable, pathOf, stepFromPath, type Step } from "./navigation/steps";
import { clearConsultation, loadConsultation, saveConsultation } from "./session/currentConsultation";
import { excludedNote } from "./text";
import type { ActivityProceduresResponse, ConsultationRequest, ConsultationResponse, ContextAnswers, SourceReference } from "./types";

/** Official site of the City's procedures, the source the guidance cites. */
const OFFICIAL_PROCEDURES_URL = "https://buenosaires.gob.ar/gobierno/tramites";
const OPEN_DATA_URL = "https://data.buenosaires.gob.ar/";
const MAY_APPLY_HINT = "Este trámite depende de tus respuestas. Contestá las preguntas de arriba para saber si te aplica.";

type ChatMessage = { role: "user" | "bot"; text: string; sourceIds?: string[] };

const SUGGESTED_QUESTIONS = [
  "¿Qué documentos necesito?",
  "¿Cuánto tarda la habilitación?",
  "¿Necesito aptitud ambiental?",
  "¿Está permitido el rubro en esta zona?",
];

type ProceduresLoad = { procedures: ActivityProceduresResponse | null; error: string | null };

/** Official procedures of the picked activity; a failure keeps the general guidance and explains why. */
async function loadActivityProcedures(slug: string | null | undefined): Promise<ProceduresLoad> {
  if (!slug) return { procedures: null, error: null };
  try {
    return { procedures: await getActivityProcedures(slug), error: null };
  } catch (err) {
    return { procedures: null, error: describeError(err) };
  }
}

function toSourceReference(data: ActivityProceduresResponse): SourceReference {
  return { id: "caba-tramites", title: data.source.name, publisher: "Gobierno de la Ciudad de Buenos Aires", url: data.source.url, note: data.source.license };
}

/** Brief summary kept in the history: what the search found, not the whole response. */
function historySummary(response: ConsultationResponse, procedures: ActivityProceduresResponse | null): string {
  if (procedures) return `${procedures.activity.name}: ${procedures.procedures.length} trámites oficiales`;
  return response.summary.length > 120 ? `${response.summary.slice(0, 117)}…` : response.summary;
}

function greeting(response: ConsultationResponse): ChatMessage {
  return { role: "bot", text: `Hola. Puedo ayudarte a revisar la orientación de tu consulta sobre ${response.interpretedActivity} en ${response.normalizedAddress}. ¿Qué te gustaría saber?` };
}

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();
  // The consultation of this tab survives a reload: restore it once, before the first render.
  const [saved] = useState(() => loadConsultation());
  const [query, setQuery] = useState<ConsultationRequest>(saved?.query ?? { activity: "", address: "" });
  const [result, setResult] = useState<ConsultationResponse | null>(saved?.result ?? null);
  const [activityProcedures, setActivityProcedures] = useState<ActivityProceduresResponse | null>(saved?.activityProcedures ?? null);
  const [proceduresError, setProceduresError] = useState<string | null>(saved?.proceduresError ?? null);
  const [contextAnswers, setContextAnswers] = useState<ContextAnswers>(saved?.contextAnswers ?? {});
  const [refining, setRefining] = useState(false);
  const [refineError, setRefineError] = useState(false);
  const refineRequest = useRef(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [checked, setChecked] = useState<string[]>(saved?.checked ?? []);
  const [checkedRequirements, setCheckedRequirements] = useState<string[]>(saved?.checkedRequirements ?? []);
  const [messages, setMessages] = useState<ChatMessage[]>(saved ? [greeting(saved.result)] : []);
  const [suggested, setSuggested] = useState<string[]>(SUGGESTED_QUESTIONS);
  const [question, setQuestion] = useState("");
  const [assistantBusy, setAssistantBusy] = useState(false);
  const chatLog = useRef<HTMLDivElement>(null);
  const history = useSearchHistory();
  // Values the form starts with after reopening a search from the history (and its remount key).
  const [prefill, setPrefill] = useState<{ key: number; request: ConsultationRequest } | null>(null);
  const step = stepFromPath(location.pathname);
  const stepState = { analyzing: busy, hasResult: !!result };

  function goTo(target: Step) {
    navigate(pathOf(target));
  }

  useEffect(() => {
    if (!result) {
      clearConsultation();
      return;
    }
    saveConsultation({ query, result, activityProcedures, proceduresError, contextAnswers, checked, checkedRequirements });
  }, [query, result, activityProcedures, proceduresError, contextAnswers, checked, checkedRequirements]);

  // Client-side navigation does not scroll to #anchors on its own (used by the footer links).
  useEffect(() => {
    if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView({ block: "start" });
  }, [location]);

  const guidanceCount = activityProcedures?.procedures.length ?? result?.steps.length ?? 0;
  const progress = useMemo(() => guidanceCount
    ? Math.round((checked.length / guidanceCount) * 100) : 0, [checked, guidanceCount]);
  const officialSources = useMemo(
    () => (activityProcedures ? [toSourceReference(activityProcedures)] : []),
    [activityProcedures],
  );
  const allSources = useMemo(
    () => [...(result?.sources ?? []), ...officialSources],
    [result, officialSources],
  );
  const discardedNote = activityProcedures
    ? excludedNote(activityProcedures.excluded, activityProcedures.excluded_count) : null;

  async function handleSubmit(data: ConsultationRequest) {
    setQuery(data);
    setResult(null);
    setActivityProcedures(null);
    setProceduresError(null);
    setContextAnswers({});
    setRefineError(false);
    setChecked([]);
    setCheckedRequirements([]);
    setMessages([]);
    setSuggested(SUGGESTED_QUESTIONS);
    setQuestion("");
    setError("");
    setBusy(true);
    goTo(2);
    try {
      const [response, load] = await Promise.all([
        submitConsultation(data), loadActivityProcedures(data.activitySlug),
      ]);
      setResult(response);
      setActivityProcedures(load.procedures);
      setProceduresError(load.error);
      history.record({
        activity: data.activity, address: data.address, activitySlug: data.activitySlug ?? null, point: data.point ?? null,
        summary: historySummary(response, load.procedures), searchedAt: new Date().toISOString(),
      });
      setMessages([greeting(response)]);
      goTo(3);
    } catch (err) {
      setError(describeError(err) ?? "");
      // The failed analysis should not stay in the history: Back would land on an empty step.
      navigate(HOME_PATH, { replace: true });
    } finally {
      setBusy(false);
    }
  }

  async function answerContext(id: string, value: boolean | null) {
    if (!activityProcedures) return;
    const { [id]: _previous, ...rest } = contextAnswers;
    const answers = value === null ? rest : { ...rest, [id]: value };
    setContextAnswers(answers);
    setRefining(true);
    setRefineError(false);
    // Only the latest answer wins when the person clicks faster than the API responds.
    const requestId = ++refineRequest.current;
    try {
      const refined = await getActivityProcedures(activityProcedures.activity.slug, answers);
      if (requestId !== refineRequest.current) return;
      setActivityProcedures(refined);
      const ids = new Set(refined.procedures.map(({ procedure }) => procedure.id));
      setChecked(old => old.filter(checkedId => ids.has(checkedId)));
    } catch {
      if (requestId === refineRequest.current) setRefineError(true);
    } finally {
      if (requestId === refineRequest.current) setRefining(false);
    }
  }

  /** "Ver": fills the form with the saved search and runs it again, which also gives the assistant a fresh consultation. */
  function openFromHistory(entry: HistoryEntry) {
    const request: ConsultationRequest = { activity: entry.activity, address: entry.address, point: entry.point, activitySlug: entry.activitySlug };
    setPrefill(current => ({ key: (current?.key ?? 0) + 1, request }));
    void handleSubmit(request);
  }

  function startOver() {
    goTo(1);
    setPrefill(null);
    setQuery({ activity: "", address: "" });
    setResult(null);
    setActivityProcedures(null);
    setProceduresError(null);
    setContextAnswers({});
    setRefineError(false);
    setChecked([]);
    setCheckedRequirements([]);
    setMessages([]);
    setSuggested(SUGGESTED_QUESTIONS);
    setQuestion("");
    setError("");
  }

  useEffect(() => {
    chatLog.current?.lastElementChild?.scrollIntoView({ block: "nearest" });
  }, [messages, assistantBusy]);

  async function askAssistant(text: string) {
    const trimmed = text.trim();
    if (!result || !trimmed || assistantBusy) return;
    setMessages(current => [...current, { role: "user", text: trimmed }]);
    setQuestion("");
    setAssistantBusy(true);
    try {
      const response = await submitFollowUp(result.consultationId, { question: trimmed });
      setMessages(current => [...current, { role: "bot", text: response.answer, sourceIds: response.sourceIds }]);
    } catch (err) {
      const message = describeError(err);
      if (message) setMessages(current => [...current, { role: "bot", text: message }]);
    } finally {
      setAssistantBusy(false);
    }
  }

  function askSuggestion(text: string) {
    setSuggested(current => current.filter(item => item !== text));
    void askAssistant(text);
  }

  function handleAskSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void askAssistant(question);
  }

  function messageSources(sourceIds?: string[]): SourceReference[] {
    if (!sourceIds?.length) return [];
    return sourceIds
      .map(id => allSources.find(source => source.id === id))
      .filter((source): source is SourceReference => !!source);
  }

  // Unknown addresses and steps without data to show (e.g. opening /orientacion with no consultation) go home.
  if (step === null || !isStepAvailable(step, stepState)) return <Navigate to={HOME_PATH} replace />;

  const queryBar = step >= 3 && (
    <div className="query-bar">
      <div className="query-bar__summary">
        <span className="query-bar__label">Tu consulta</span>
        <span className="query-pill">{query.activity}</span>
        <span className="query-pill">{query.address}</span>
        <button className="text-button" onClick={() => goTo(1)} type="button">Editar consulta</button>
        <button className="text-button" onClick={() => void handleSubmit(query)} type="button" disabled={busy}
          title="Volver a consultar por si cambió algo">Actualizar</button>
      </div>
      <nav className="tabs" aria-label="Secciones de la consulta">
        {STEPS.slice(2).map(item => (
          <button key={item.path} className={step === item.step ? "is-active" : ""} aria-current={step === item.step ? "page" : undefined}
            onClick={() => goTo(item.step)} type="button">{item.label}</button>
        ))}
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
        {STEPS.map(({ step: number, label }) => {
          const current = number === step;
          const completed = number < step;
          const available = isStepAvailable(number, stepState);
          return (
            // aria-disabled instead of disabled: unavailable steps stay focusable so screen readers announce them.
            <button type="button" key={label} className={`step ${current ? "active" : ""} ${completed ? "completed" : ""}`}
              aria-current={current ? "step" : undefined} aria-disabled={!available || undefined}
              onClick={() => { if (available && !current) goTo(number); }}>
              <span className="step-number" aria-hidden="true">{completed ? "✓" : number}</span>
              <span>{label}</span>
              <span className="sr-only">{current ? " (paso actual)" : !available ? " (no disponible todavía)" : completed ? " (completado)" : ""}</span>
            </button>
          );
        })}
      </nav>

      {queryBar}

      <main className={`main-content ${step >= 3 ? "main-content--wide" : ""}`}>
        <ErrorBoundary variant="section" resetKey={step}>
        {step === 1 && (
          <section className={`hero ${history.entries.length ? "hero--with-history" : ""}`}>
            <p className="eyebrow">TU ACTIVIDAD · TU DIRECCIÓN · TU PRÓXIMO PASO</p>
            <h1>Contanos qué querés hacer <span>y dónde.</span></h1>
            <p className="hero-description">Indicá la actividad y la dirección. Conco organiza la información disponible para orientarte sobre los próximos pasos de tu emprendimiento.</p>
            <div className="section-heading">
              <span className="section-icon">01</span>
              <div><h2>Empecemos por tu idea</h2><p>Completá los datos para iniciar tu consulta.</p></div>
            </div>
            <div className={`query-layout ${history.entries.length ? "query-layout--with-history" : ""}`}>
              <div>
                <QueryForm key={prefill?.key ?? 0} initial={prefill?.request} busy={busy} onSubmit={handleSubmit} />
                {error && <p className="error-message" role="alert">{error}</p>}
              </div>
              <RecentSearches entries={history.entries} busy={busy} onOpen={openFromHistory} onClear={history.clear} />
            </div>
            <p className="security-note"><span className="security-dot" />Tus datos se utilizan para preparar esta consulta.</p>
            <div className="features" id="como-funciona">
              <article className="feature"><div className="feature__icon" /><div><h2>Varias fuentes, una respuesta</h2><p>Cruzamos trámites, normativa y datos territoriales al mismo tiempo.</p></div></article>
              <article className="feature"><div className="feature__icon" /><div><h2>Cada dato con su fuente</h2><p>Vas a ver de dónde sale cada requisito y cada afirmación.</p></div></article>
              <article className="feature"><div className="feature__icon" /><div><h2>Tu ubicación en el mapa</h2><p>Te mostramos la zona consultada con sus capas de información.</p></div></article>
            </div>
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
            <AnalysisSources running={busy} />
            <button className="secondary" type="button" onClick={() => goTo(1)} disabled={busy}>Volver a editar</button>
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
              {proceduresError && <div className="notice"><span className="notice-icon">i</span><div><strong>No pudimos cargar los trámites oficiales</strong><p>{proceduresError} Mientras tanto, te mostramos una orientación general.</p></div></div>}
              {activityProcedures && (
                <ContextQuestions questions={activityProcedures.questions} busy={refining} onAnswer={answerContext} />
              )}
              {refineError && <div className="notice"><span className="notice-icon">i</span><div><strong>No pudimos actualizar los trámites</strong><p>Seguimos mostrando la lista anterior. Probá responder de nuevo.</p></div></div>}
              {discardedNote && <p className="excluded-note" aria-live="polite">{discardedNote}</p>}
              <div className="guidance-list">
                {activityProcedures ? activityProcedures.procedures.map(({ procedure, note, status }, index) => (
                  <article className="guidance-card" key={procedure.id}>
                    <div className="guidance-card__top">
                      <span className="guidance-number">{String(index + 1).padStart(2, "0")}</span>
                      {status === "applies"
                        ? <span className="guidance-tag">TRÁMITE OFICIAL</span>
                        : <>
                          <span className="guidance-tag guidance-tag--maybe">PUEDE APLICAR</span>
                          <span className="guidance-tag-hint">{MAY_APPLY_HINT}</span>
                        </>}
                    </div>
                    <h2>{procedure.title}</h2>
                    <p className="guidance-note"><strong>Cuándo aplica:</strong> {note}</p>
                    <p>{procedure.summary}</p>
                    <a className="procedure-link" href={procedure.official_url} target="_blank" rel="noreferrer">Ver el trámite en buenosaires.gob.ar <span aria-hidden="true">↗</span></a>
                    <label className="review-check">
                      <input type="checkbox" checked={checked.includes(procedure.id)}
                        onChange={e => setChecked(old => e.target.checked ? [...old, procedure.id] : old.filter(id => id !== procedure.id))} />
                      <span>Marcar como revisado</span>
                    </label>
                  </article>
                )) : result.steps.length ? result.steps.map((item, index) => (
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
                <div><strong>Tu avance</strong><span>{checked.length} de {guidanceCount} revisados</span></div>
                <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
              </div>
              <div className="orientation-actions">
                <button className="secondary" type="button" onClick={() => goTo(2)}>← Volver al análisis</button>
                <button className="primary" type="button" onClick={() => goTo(4)}>Ver mapa →</button>
              </div>
            </section>
            <aside className="side-column">
              <section className="panel understood-card">
                <h2>Lo que entendimos</h2>
                <div className="result-detail"><span>Actividad</span><p>{activityProcedures?.activity.name ?? result.interpretedActivity}</p></div>
                <div className="result-detail"><span>Ubicación</span><p>{result.normalizedAddress}</p></div>
                <p className="small-note">{activityProcedures
                  ? "Estos son trámites que suelen aplicar a esta actividad. Es una orientación general: verificá los requisitos con el organismo responsable."
                  : result.summary}</p>
              </section>
              <RequirementsChecklist
                requirements={activityProcedures?.requirements ?? []}
                note={activityProcedures?.requirements_note ?? ""}
                checked={checkedRequirements}
                onToggle={id => setCheckedRequirements(old =>
                  old.includes(id) ? old.filter(checkedId => checkedId !== id) : [...old, id])}
              />
              <OfficialSources sources={officialSources} />
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
              <button className="secondary" type="button" onClick={() => goTo(3)}>← Volver a orientación</button>
              <button className="primary" type="button" onClick={() => goTo(5)}>Consultar al asistente →</button>
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
              <div className="chat-log" ref={chatLog} aria-live="polite">
                {messages.map((message, index) => message.role === "user" ? (
                  <div className="chat-msg chat-msg--user" key={index}><p>{message.text}</p></div>
                ) : (
                  <article className="chat-msg chat-msg--bot" key={index}>
                    <span className="chat-msg__who">Asistente Conco</span>
                    <p>{message.text}</p>
                    {messageSources(message.sourceIds).length > 0 && (
                      <div className="chat-trace">
                        <span className="chat-trace__label">Fuentes de esta respuesta</span>
                        <ul>
                          {messageSources(message.sourceIds).map(source => (
                            <li key={source.id}>
                              <a href={source.url} target="_blank" rel="noreferrer">{source.title} <span aria-hidden="true">↗</span></a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </article>
                ))}
                {assistantBusy && <p className="chat-typing">Buscando en las fuentes oficiales…</p>}
              </div>
              {suggested.length > 0 && (
                <div className="suggest">
                  <span className="hint">Preguntas de seguimiento</span>
                  <div className="example-chips">
                    {suggested.map(item => (
                      <button key={item} type="button" className="chip" onClick={() => askSuggestion(item)}>{item}</button>
                    ))}
                  </div>
                </div>
              )}
              <form className="assistant-form" onSubmit={handleAskSubmit}>
                <label htmlFor="assistant-question">Tu pregunta</label>
                <input id="assistant-question" name="question" type="text" value={question}
                  onChange={e => setQuestion(e.target.value)}
                  placeholder="Escribí tu pregunta…" autoComplete="off" />
                <button className="primary" type="submit" disabled={assistantBusy || !question.trim()}>{assistantBusy ? "Enviando…" : "Preguntar →"}</button>
              </form>
              {allSources.length > 0 && (
                <div className="chat-sources">
                  <span className="hint">Fuentes disponibles</span>
                  <ul>
                    {allSources.map(source => (
                      <li key={source.id}>
                        <a href={source.url} target="_blank" rel="noreferrer">{source.title} <span aria-hidden="true">↗</span></a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <p className="small-note">La respuesta depende de las integraciones disponibles. No reemplaza la consulta ante organismos oficiales.</p>
              <section className="chat-how">
                <h2>Cómo responde</h2>
                <p>Usa la información de la consulta y las fuentes oficiales conectadas. Si no hay una fuente que responda, te lo dice en lugar de inventar una respuesta.</p>
              </section>
            </div>
            <div className="orientation-actions"><button className="secondary" type="button" onClick={() => goTo(4)}>← Volver al mapa</button><button className="primary" type="button" onClick={startOver}>Nueva consulta →</button></div>
          </section>
        )}
        </ErrorBoundary>
      </main>

      <footer className="footer">
        <div className="footer__inner">
          <div className="footer__brand">
            <p>Consultá qué necesitás para habilitar tu comercio en la Ciudad de Buenos Aires, con información de fuentes oficiales.</p>
            <h2>Seguinos</h2>
            {/* No official accounts yet: icons are shown without a fake link. */}
            <div className="social" title="Próximamente">
              <span className="social__item" role="img" aria-label="Instagram (próximamente)"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r="1" fill="currentColor" stroke="none"/></svg></span>
              <span className="social__item" role="img" aria-label="Facebook (próximamente)"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg></span>
              <span className="social__item" role="img" aria-label="X (próximamente)"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M4 4l16 16M20 4L4 20"/></svg></span>
            </div>
          </div>
          <nav className="footer__col" aria-label="Consultas">
            <h2>Consultas</h2>
            <Link to={HOME_PATH} onClick={event => { event.preventDefault(); startOver(); }}>Habilitación de comercios</Link>
            <Link to={result ? pathOf(3) : HOME_PATH}>Trámites y requisitos</Link>
            <Link to={result ? pathOf(4) : HOME_PATH}>Mapa de la Ciudad</Link>
            <Link to={result ? pathOf(5) : `${HOME_PATH}#como-funciona`}>Preguntas frecuentes</Link>
          </nav>
          <nav className="footer__col" aria-label="Ayuda">
            <h2>Ayuda</h2>
            <Link to={`${HOME_PATH}#como-funciona`}>Cómo funciona</Link>
            <a href={OFFICIAL_PROCEDURES_URL} target="_blank" rel="noreferrer">Fuentes oficiales <span aria-hidden="true">↗</span></a>
            {/* No page exists yet for these: plain text instead of links that lead nowhere. */}
            <span>Centro de ayuda (próximamente)</span>
            <span>Accesibilidad (próximamente)</span>
          </nav>
          <div className="footer__col">
            <h2>Contacto</h2>
            <span>[Teléfono de atención]</span>
            <span>[Correo de contacto]</span>
            <span>[Horario de atención]</span>
          </div>
        </div>
        <div className="footer__bar">
          <span>© 2026 ConCo — Orientación inicial para emprendedores</span>
          <span>Términos y condiciones (próximamente)</span>
          <span>Política de privacidad (próximamente)</span>
          <a href={OPEN_DATA_URL} target="_blank" rel="noreferrer">Datos abiertos <span aria-hidden="true">↗</span></a>
        </div>
        <div className="footer__logo-wrap">
          <button className="brand" type="button" onClick={startOver} aria-label="Volver al inicio de Conco">
            <img src="/conco-logo.png" alt="Conco" className="footer__logo" />
          </button>
        </div>
      </footer>
    </div>
  );
}
