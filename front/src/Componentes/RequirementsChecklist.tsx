import { useMemo } from 'react';
import type { Requirement } from '../types';
import { groupRequirements, SHARED_GROUP_ID } from './requirementGroups';

type Props = {
  requirements: Requirement[];
  procedures: { id: string; title: string }[];
  note: string;
  checked: string[];
  onToggle: (id: string) => void;
  /** Ids of the groups currently expanded. */
  openGroups: string[];
  onToggleGroup: (id: string, open: boolean) => void;
};

function percent(done: number, total: number) {
  return total ? Math.round((done / total) * 100) : 0;
}

/**
 * "Qué tenés que conseguir" tab: the aggregated requirements grouped by the
 * procedure that asks for them, each group collapsible with its own progress.
 * Checkbox state is owned by the caller so it stays independent from the
 * procedures checklist. Requirement bodies and headings are plain text from
 * the API; no third-party HTML is ever injected here (RN-05).
 */
export default function RequirementsChecklist({ requirements, procedures, note, checked, onToggle, openGroups, onToggleGroup }: Props) {
  const groups = useMemo(() => groupRequirements(requirements, procedures), [requirements, procedures]);

  return (
    <section className="requirements-tab" aria-label="Qué tenés que conseguir">
      <p className="requirements-intro">Antes de empezar, esto es lo que tenés que conseguir, agrupado por el trámite que lo pide.</p>
      {groups.length > 0 && (
        <>
          <div className="progress-panel requirements-progress">
            <div>
              <strong>Tu avance</strong>
              <span>{checked.length} de {requirements.length} requerimientos marcados</span>
            </div>
            <div className="progress-track"><span style={{ width: `${percent(checked.length, requirements.length)}%` }} /></div>
          </div>
          <div className="requirement-groups">
            {groups.map(group => {
              const done = group.items.filter(item => checked.includes(item.id)).length;
              return (
                <details key={group.id} id={`requisitos-${group.id}`} className="requirement-group"
                  open={openGroups.includes(group.id)}
                  onToggle={event => onToggleGroup(group.id, event.currentTarget.open)}>
                  <summary>
                    <span className="requirement-group__title">{group.title}</span>
                    <span className="requirement-group__count">{done} de {group.items.length}</span>
                  </summary>
                  {group.url && (
                    <a className="procedure-link requirement-group__link" href={group.url} target="_blank" rel="noreferrer">
                      Ver el trámite en buenosaires.gob.ar <span aria-hidden="true">↗</span>
                    </a>
                  )}
                  <ul className="requirements-list">
                    {group.items.map(requirement => (
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
                        {group.id === SHARED_GROUP_ID && (
                          <div className="requirement-origins">
                            <span>Lo piden:</span>
                            {requirement.origins.map(origin => (
                              <a key={origin.procedure_id} href={origin.official_url} target="_blank" rel="noreferrer">
                                {origin.procedure_title} <span aria-hidden="true">↗</span>
                              </a>
                            ))}
                          </div>
                        )}
                      </li>
                    ))}
                  </ul>
                </details>
              );
            })}
          </div>
        </>
      )}
      <p className="small-note requirements-note">{note}</p>
    </section>
  );
}
