import { nextPending } from './orientationProgress';

type Item = { id: string; title: string };

type Props = {
  activity: string;
  address: string;
  /** Procedures (or general steps) in the order they are listed. */
  procedures: Item[];
  reviewed: string[];
  requirementsTotal: number;
  requirementsChecked: number;
  onOpenProcedure: (id: string) => void;
  onOpenRequirements: () => void;
  onOpenMap: () => void;
  onOpenAssistant: () => void;
};

function percent(done: number, total: number) {
  return total ? Math.round((done / total) * 100) : 0;
}

/** "Tu avance" panel of the orientation: what was understood, progress, next procedure and the other views. */
export default function ProgressSidebar({
  activity, address, procedures, reviewed, requirementsTotal, requirementsChecked,
  onOpenProcedure, onOpenRequirements, onOpenMap, onOpenAssistant,
}: Props) {
  const next = nextPending(procedures, reviewed);
  const reviewedCount = procedures.filter(item => reviewed.includes(item.id)).length;

  return (
    <section className="panel progress-sidebar" aria-label="Tu avance">
      <h2>Tu avance</h2>
      <div className="result-detail"><span>Actividad</span><p>{activity}</p></div>
      <div className="result-detail"><span>Ubicación</span><p>{address}</p></div>

      {procedures.length > 0 && (
        <div className="progress-sidebar__block">
          <div className="progress-sidebar__row"><strong>Trámites revisados</strong><span>{reviewedCount} de {procedures.length}</span></div>
          <div className="progress-track"><span style={{ width: `${percent(reviewedCount, procedures.length)}%` }} /></div>
        </div>
      )}

      {requirementsTotal > 0 && (
        <div className="progress-sidebar__block">
          <div className="progress-sidebar__row"><strong>Lo que tenés que conseguir</strong><span>{requirementsChecked} de {requirementsTotal}</span></div>
          <div className="progress-track"><span style={{ width: `${percent(requirementsChecked, requirementsTotal)}%` }} /></div>
          <button className="text-button progress-sidebar__link" type="button" onClick={onOpenRequirements}>Ver la lista completa →</button>
        </div>
      )}

      {procedures.length > 0 && (
        <div className="progress-sidebar__block">
          <span className="progress-sidebar__label">Siguiente trámite</span>
          {next
            ? <button className="text-button progress-sidebar__next" type="button" onClick={() => onOpenProcedure(next.id)}>{next.title} →</button>
            : <p className="progress-sidebar__done">Revisaste todos los trámites.</p>}
        </div>
      )}

      <div className="progress-sidebar__actions">
        <button className="secondary" type="button" onClick={onOpenMap}>Ver mapa</button>
        <button className="secondary" type="button" onClick={onOpenAssistant}>Preguntar al asistente</button>
      </div>
    </section>
  );
}
