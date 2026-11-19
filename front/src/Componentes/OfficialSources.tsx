import type { SourceReference } from '../types';

/**
 * Slim list of the real sources of the activity's procedures (RN-05). Each
 * entry is built from the `OfficialSource` of GET .../procedures through
 * `toSourceReference`; the license travels in `note`.
 */
export default function OfficialSources({ sources }: { sources: SourceReference[] }) {
  if (sources.length === 0) return null;
  return (
    <section className="panel official-sources-panel">
      <h2>Fuentes oficiales</h2>
      <ul className="official-sources-list">
        {sources.map(source => (
          <li className="official-source" key={source.id}>
            <a href={source.url} target="_blank" rel="noreferrer">
              {source.title} <span aria-hidden="true">↗</span>
            </a>
            {source.note && <span className="official-source-license">{source.note}</span>}
          </li>
        ))}
      </ul>
    </section>
  );
}
