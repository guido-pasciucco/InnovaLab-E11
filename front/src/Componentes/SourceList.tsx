import type { SourceReference } from '../types';
export default function SourceList({ sources }: { sources: SourceReference[] }) {
  return <section className="panel"><h2>Fuentes consultadas</h2>
    <ul className="source-list">{sources.map(source => <li key={source.id}>
      <strong>{source.title}</strong><span>{source.publisher}</span>
      {source.note && <p>{source.note}</p>}
      <a href={source.url} target="_blank" rel="noreferrer">Abrir fuente ↗</a>
    </li>)}</ul>
  </section>;
}
