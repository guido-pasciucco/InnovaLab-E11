//Interfaz principal y formulario de consulta//

import { useState, type FormEvent } from 'react';
import QueryForm from './components/QueryForm';
import MapPanel from './components/MapPanel';
import SourceList from './components/SourceList';
import { submitConsultation, submitFollowUp } from './api/client';
import type { ConsultationRequest, ConsultationResponse } from './types';

export default function App() {
  const [result, setResult] = useState<ConsultationResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [question, setQuestion] = useState('');
  const [followUp, setFollowUp] = useState('');
  const [followBusy, setFollowBusy] = useState(false);

  async function consult(payload: ConsultationRequest) {
    setBusy(true); setError(''); setFollowUp(''); setResult(null);
    try { setResult(await submitConsultation(payload)); }
    catch (e) { setError(e instanceof Error ? e.message : 'No se pudo completar la consulta.'); }
    finally { setBusy(false); }
  }

  async function askFollowUp(event: FormEvent) {
    event.preventDefault();
    if (!result || !question.trim()) return;
    setFollowBusy(true); setFollowUp('');
    try {
      const answer = await submitFollowUp(result.consultationId, { question: question.trim() });
      setFollowUp(answer.answer + (answer.limitations?.length ? `\n\nLimitación: ${answer.limitations.join(' ')}` : ''));
      setQuestion('');
    } catch (e) { setError(e instanceof Error ? e.message : 'Falló la pregunta adicional.'); }
    finally { setFollowBusy(false); }
  }

  return <main className="shell">
    <header className="topbar"><a className="brand" href="#"><span className="brand-mark">c</span> conco</a><span>Orientación para emprender</span></header>
    <section className="hero"><p className="eyebrow">TU ACTIVIDAD · TU DIRECCIÓN · TU PRÓXIMO PASO</p>
      <h1>Entendé qué necesitás<br />para poner en marcha tu negocio.</h1>
      <p>Consultá procedimientos y contexto territorial desde un solo lugar.</p>
    </section>
    <QueryForm onSubmit={consult} busy={busy} />
    {error && <div className="alert" role="alert">{error}</div>}
    {result && <div className="results">
      <section className="panel"><p className="eyebrow">ORIENTACIÓN PARA TU CONSULTA</p>
        <h2>{result.interpretedActivity}</h2><p className="address-line">{result.normalizedAddress}</p>
        <p>{result.summary}</p>
        {result.limitations.map(item => <p className="limitation" key={item}>ⓘ {item}</p>)}
      </section>
      <div className="results-grid">
        <section className="panel"><h2>Pasos sugeridos</h2><ol className="steps">{result.steps.map((step, i) => <li key={step.id}>
          <span className="step-number">{i + 1}</span><div><h3>{step.title}</h3><p>{step.description}</p>
          {step.documents?.length ? <p className="hint"><b>Prepará:</b> {step.documents.join('; ')}</p> : null}</div>
        </li>)}</ol></section>
        <MapPanel point={result.point} address={result.normalizedAddress} features={result.territorialFeatures} />
      </div>
      <SourceList sources={result.sources} />
      <section className="panel"><h2>¿Tenés otra pregunta?</h2><form className="follow-form" onSubmit={askFollowUp}>
        <input value={question} onChange={e => setQuestion(e.target.value)} placeholder="Preguntá algo sobre esta orientación…" required />
        <button className="secondary" disabled={followBusy}>{followBusy ? 'Consultando…' : 'Preguntar'}</button>
      </form>{followUp && <p className="follow-answer">{followUp}</p>}</section>
    </div>}
    <footer>conco · Prototipo frontend. Confirmá siempre los requisitos con la fuente oficial vigente.</footer>
  </main>;
}
