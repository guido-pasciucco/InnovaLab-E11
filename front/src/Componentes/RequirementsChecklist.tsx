import { useMemo } from 'react';
import type { Requirement } from '../types';

type Props = {
  requirements: Requirement[];
  note: string;
  checked: string[];
  onToggle: (id: string) => void;
};

/**
 * Aggregated "Antes de empezar" checklist. Its checkbox state and progress are
 * owned by the caller so they stay independent from the procedures checklist.
 * Requirement bodies and headings are plain text from the API; no third-party
 * HTML is ever injected here (RN-05).
 */
export default function RequirementsChecklist({ requirements, note, checked, onToggle }: Props) {
  const progress = useMemo(
    () => requirements.length
      ? Math.round((checked.length / requirements.length) * 100)
      : 0,
    [checked, requirements],
  );

  return (
    <section className="panel requirements-panel">
      <h2>Antes de empezar: lo que tenés que conseguir</h2>
      {requirements.length > 0 && (
        <>
          <ul className="requirements-list">
            {requirements.map(requirement => (
              <li className="requirement-item" key={requirement.id}>
                <label className="requirement-check">
                  <input
                    type="checkbox"
                    checked={checked.includes(requirement.id)}
                    onChange={() => onToggle(requirement.id)}
                  />
                  <span className="requirement-text">
                    {requirement.heading && <strong className="requirement-heading">{requirement.heading}</strong>}
                    <span>{requirement.text}</span>
                  </span>
                </label>
                {requirement.origins.length > 0 && (
                  <div className="requirement-origins">
                    {requirement.origins.map(origin => (
                      <a key={origin.procedure_id} href={origin.official_url} target="_blank" rel="noreferrer">
                        del trámite: {origin.procedure_title} <span aria-hidden="true">↗</span>
                      </a>
                    ))}
                  </div>
                )}
              </li>
            ))}
          </ul>
          <div className="progress-panel requirements-progress">
            <div>
              <strong>Tu avance</strong>
              <span>{checked.length} de {requirements.length} requerimientos marcados</span>
            </div>
            <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
          </div>
        </>
      )}
      <p className="small-note requirements-note">{note}</p>
    </section>
  );
}
