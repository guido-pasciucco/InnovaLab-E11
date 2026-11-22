import { useEffect, useState } from "react";
import { relativeTime, type HistoryEntry } from "../history/searchHistory";

const VISIBLE_ITEMS = 5;
const DESKTOP_QUERY = "(min-width: 1100px)";

type Props = {
  entries: HistoryEntry[];
  busy: boolean;
  onOpen: (entry: HistoryEntry) => void;
  onClear: () => void;
};

function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => typeof window !== "undefined" && window.matchMedia(query).matches);
  useEffect(() => {
    const media = window.matchMedia(query);
    const update = () => setMatches(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, [query]);
  return matches;
}

/**
 * "Búsquedas recientes" on the Consulta step: a side card on desktop, a collapsible section on mobile.
 * Hidden when there is no history.
 */
export default function RecentSearches({ entries, busy, onOpen, onClear }: Props) {
  const desktop = useMediaQuery(DESKTOP_QUERY);
  const [showAll, setShowAll] = useState(false);
  if (!entries.length) return null;

  const title = `Búsquedas recientes (${entries.length})`;
  const visible = showAll ? entries : entries.slice(0, VISIBLE_ITEMS);
  const content = (
    <>
      <ul className="recent-searches__list">
        {visible.map(entry => (
          <li className="recent-searches__item" key={entry.id} title={entry.summary || undefined}>
            <span className="query-pill recent-searches__label">{entry.activity} · {entry.address}</span>
            <time className="recent-searches__time" dateTime={entry.searchedAt}>{relativeTime(entry.searchedAt)}</time>
            <button className="chip" type="button" disabled={busy} onClick={() => onOpen(entry)}
              aria-label={`Ver ${entry.activity} en ${entry.address}`}>Ver</button>
          </li>
        ))}
      </ul>
      {entries.length > VISIBLE_ITEMS && (
        <button className="text-button" type="button" aria-expanded={showAll} onClick={() => setShowAll(value => !value)}>
          {showAll ? "Ver menos" : `Ver todas (${entries.length})`}
        </button>
      )}
      <p className="small-note">Se guardan solo en este navegador: no se envían a ningún servidor.</p>
      <button className="secondary recent-searches__clear" type="button" onClick={onClear}>Limpiar historial</button>
    </>
  );

  if (desktop) {
    return (
      <aside className="panel recent-searches" aria-labelledby="recent-searches-title">
        <h2 id="recent-searches-title">{title}</h2>
        {content}
      </aside>
    );
  }
  return (
    <details className="panel recent-searches">
      <summary>{title}</summary>
      {content}
    </details>
  );
}
