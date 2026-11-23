import type { SourceReference } from '../types';

/**
 * One-line citation of the real sources of the activity's procedures (RN-05).
 * The City's data is CC BY 2.5 AR, which requires citing it, so this line must
 * stay visible next to the procedures. The license travels in `note`.
 */
export default function OfficialSources({ sources }: { sources: SourceReference[] }) {
  if (sources.length === 0) return null;
  return (
    <p className="source-line">
      Fuente:{' '}
      {sources.map((source, index) => (
        <span key={source.id}>
          {index > 0 && ' · '}
          <a href={source.url} target="_blank" rel="noreferrer">
            {source.title} <span aria-hidden="true">↗</span>
          </a>
          {source.note && <> · {source.note}</>}
        </span>
      ))}
    </p>
  );
}
