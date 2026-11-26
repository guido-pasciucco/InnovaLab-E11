import { useEffect, useRef, useState } from "react";
import { getParcelGeometry, getRubroReferencias, getUseTable } from "../api/client";
import { describeError } from "../api/errors";
import { normalize } from "../history/searchHistory";
import type {
  GeoPoint, RubroReferencias, SourceReference, UseTableCategory, UseTableResponse,
} from "../types";

/** Fallback citation: the panel cites the official source even before the API answers. */
export const OFFICIAL_USE_TABLE_SOURCE: SourceReference = {
  id: "usig-ciudad-3d",
  title: "Ciudad 3D — Cuadro de usos",
  publisher: "USIG, Gobierno de la Ciudad de Buenos Aires",
  url: "https://ciudad3d.buenosaires.gob.ar",
};

/** RN-04: orientation only; never a cadastral confirmation or a ruling on the person's activity. */
const DISCLAIMER = "Es información de referencia del Cuadro de Usos oficial de la Ciudad de Buenos Aires. " +
  "No es una confirmación catastral ni un dictamen sobre si la actividad que querés hacer está permitida en este lugar.";

export type CategoryRow = UseTableCategory & { rubroCount: number };

/**
 * Keeps the official category and rubro order; the count is derived from the visible rubros only.
 * Reuses the search-history normalization criterion so accents and capital letters do not hide a rubro (S10).
 */
export function filterCategories(categories: UseTableCategory[], query: string): CategoryRow[] {
  const needle = normalize(query);
  return categories.map(category => {
    const rubros = needle
      ? category.rubros.filter(rubro => normalize(rubro.name).includes(needle))
      : category.rubros;
    return { ...category, rubros, rubroCount: rubros.length };
  });
}

/** No query: every official rubro stays visible and counted. */
export function categoryRows(categories: UseTableCategory[]): CategoryRow[] {
  return filterCategories(categories, "");
}

/** Best-effort real geometry: never fail the use-table panel or add error UI when Catastro has no shape (S12). */
export async function publishParcelGeometry(
  data: UseTableResponse,
  signal: AbortSignal,
  onGeometry?: (geometry: GeoJSON.Geometry | null) => void,
): Promise<void> {
  if (!onGeometry || signal.aborted) return;
  if (data.smp === null) {
    onGeometry(null);
    return;
  }
  try {
    const response = await getParcelGeometry(data.smp, { signal });
    if (!signal.aborted) onGeometry(response.geometry);
  } catch {
    // A missing geometry just leaves the illustrative demo layers in place.
  }
}

export type ReferenciaKey = 'permitido_mixtura_de_usos' | 'bicicletas' | 'estacionamientos' | 'cargaydescarga' | 'observaciones';

const REFERENCIA_TITLES: Record<ReferenciaKey, string> = {
  permitido_mixtura_de_usos: "Permitido por mixtura de usos",
  bicicletas: "Bicicletas",
  estacionamientos: "Estacionamientos",
  cargaydescarga: "Carga y descarga",
  observaciones: "Observaciones",
};

/** All five official keys, in a fixed order, so the person always sees the same grouping. */
export function referenciaSections(referencias: RubroReferencias): { key: ReferenciaKey; title: string; items: string[] }[] {
  return (Object.keys(REFERENCIA_TITLES) as ReferenciaKey[]).map(key => ({
    key,
    title: REFERENCIA_TITLES[key],
    items: key === 'observaciones'
      ? (referencias.observaciones ? [referencias.observaciones] : [])
      : (referencias[key] ?? []),
  }));
}

/** An empty table is how the backend reports a point outside the served area (no SMP). */
export function useTableIsEmpty(data: UseTableResponse): boolean {
  return data.smp === null && data.categories.length === 0;
}

/** One place to turn a failed consultation into the message shown in the panel. */
export function useTableErrorMessage(error: unknown): string {
  return describeError(error) ?? (error instanceof Error ? error.message : "No pudimos consultar el cuadro de usos.");
}

export function UseTableEmptyState({ limitations }: { limitations: string[] }) {
  return (
    <div className="use-table__empty">
      <p className="small-note" role="status">
        No encontramos la parcela en el Cuadro de Usos de Ciudad 3D. Puede estar fuera del área consultada o no tener datos publicados.
      </p>
      {limitations.length > 0 && (
        <ul className="small-note">
          {limitations.map(limitation => <li key={limitation}>{limitation}</li>)}
        </ul>
      )}
    </div>
  );
}

export function UseTableError({ message }: { message: string }) {
  return (
    <div className="notice notice--error" role="alert">
      <span className="notice-icon" aria-hidden="true">!</span>
      <div><strong>No pudimos consultar el Cuadro de Usos</strong><p>{message}</p></div>
    </div>
  );
}

export function RubroReferenciasView({ referencias }: { referencias: RubroReferencias }) {
  return (
    <div className="use-table__referencias">
      <h4>Condiciones del rubro</h4>
      {referenciaSections(referencias).map(section => (
        <section key={section.key} className="use-table__group">
          <h5>{section.title}</h5>
          {section.items.length
            ? <ul>{section.items.map((item, index) => <li key={index}>{item}</li>)}</ul>
            : <p className="small-note">Sin condiciones informadas.</p>}
        </section>
      ))}
      {referencias.limitations.length > 0 && (
        <ul className="small-note">
          {referencias.limitations.map(limitation => <li key={limitation}>{limitation}</li>)}
        </ul>
      )}
    </div>
  );
}

/** Filtered category accordion, controlled by the query so the visible result can be verified without a DOM. */
export function UseTableResults({ categories, query, selected, onSelect }: {
  categories: UseTableCategory[];
  query: string;
  selected: { categoria: number; rubro: number } | null;
  onSelect: (categoria: number, rubro: number) => void;
}) {
  const [openCategoryId, setOpenCategoryId] = useState<number | null>(null);
  const rows = filterCategories(categories, query);
  const total = rows.reduce((sum, row) => sum + row.rubroCount, 0);

  if (query.trim() && total === 0) {
    return (
      <p className="small-note use-table__no-results" role="status">
        No hay rubros que coincidan con «{query}» en el cuadro de usos. Probá con otro nombre.
      </p>
    );
  }

  return (
    <ul className="use-table__categories">
      {rows.map(category => {
        const open = openCategoryId === category.id;
        const isFiltered = Boolean(query.trim());
        return (
          <li className="use-table__category" key={category.id}>
            <button
              type="button"
              className="use-table__category-toggle"
              aria-expanded={open}
              aria-controls={`use-table-rubros-${category.id}`}
              onClick={() => setOpenCategoryId(open ? null : category.id)}
            >
              <span>{category.name}</span>
              <span className="use-table__count">{category.rubroCount} {category.rubroCount === 1 ? "rubro" : "rubros"}</span>
            </button>
            {isFiltered && category.rubroCount === 0 && (
              <p className="small-note use-table__category-empty">Ningún rubro de esta categoría coincide con la búsqueda.</p>
            )}
            <ul className="use-table__rubros" id={`use-table-rubros-${category.id}`} hidden={!open}>
              {category.rubros.map(rubro => (
                <li key={rubro.id}>
                  <button
                    type="button"
                    className="use-table__rubro"
                    aria-pressed={selected?.rubro === rubro.id}
                    onClick={() => onSelect(category.id, rubro.id)}
                  >
                    {rubro.name}
                  </button>
                </li>
              ))}
            </ul>
          </li>
        );
      })}
    </ul>
  );
}

/** Parcel facts, rubro filter, official category accordion and conditions of the selected rubro. */
export function UseTableResult({ data }: { data: UseTableResponse }) {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<{ categoria: number; rubro: number } | null>(null);
  const [referencias, setReferencias] = useState<RubroReferencias | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  // A point change unmounts this subtree; the in-flight rubro request must not outlive it.
  useEffect(() => () => controllerRef.current?.abort(), []);

  function selectRubro(categoria: number, rubro: number) {
    controllerRef.current?.abort();
    setSelected({ categoria, rubro });
    setReferencias(null);
    setError(null);
    if (data.smp === null || data.mix_area === null) {
      setError("No hay datos de parcela o mixtura para consultar las condiciones de este rubro.");
      return;
    }
    const controller = new AbortController();
    controllerRef.current = controller;
    setLoading(true);
    getRubroReferencias(
      { smp: data.smp, categoria, mixtura: data.mix_area, rubro },
      { signal: controller.signal },
    )
      .then(result => { if (!controller.signal.aborted) setReferencias(result); })
      .catch((cause: unknown) => {
        const message = useTableErrorMessage(cause);
        if (!controller.signal.aborted) setError(message);
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
  }

  return (
    <div className="use-table__result">
      <dl className="use-table__facts">
        <div><dt>SMP estimado</dt><dd>{data.smp ?? "Sin SMP"}</dd></div>
        <div><dt>Dirección oficial</dt><dd>{data.official_address ?? "Sin dirección oficial"}</dd></div>
        <div><dt>Área de mixtura</dt><dd>{data.mix_area ?? "Sin dato"}</dd></div>
      </dl>
      {data.limitations.length > 0 && (
        <ul className="small-note use-table__limitations">
          {data.limitations.map(limitation => <li key={limitation}>{limitation}</li>)}
        </ul>
      )}

      <div className="use-table__filter">
        <label htmlFor="use-table-rubro-filter">Filtrar rubros por nombre</label>
        <input
          id="use-table-rubro-filter"
          type="search"
          value={query}
          placeholder="Buscar rubro por nombre…"
          onChange={event => setQuery(event.target.value)}
        />
      </div>

      <h4>Categorías del cuadro de usos</h4>
      <UseTableResults categories={data.categories} query={query} selected={selected} onSelect={selectRubro} />

      {loading && <p className="small-note" role="status">Consultando las condiciones del rubro…</p>}
      {error && <UseTableError message={error} />}
      {referencias && <RubroReferenciasView referencias={referencias} />}
    </div>
  );
}

/** Official Cuadro de Usos panel, mounted below the map hint. */
export default function UseTablePanel({
  point, onGeometry,
}: {
  point: GeoPoint | null;
  onGeometry?: (geometry: GeoJSON.Geometry | null) => void;
}) {
  const [table, setTable] = useState<UseTableResponse | null>(null);
  const [loading, setLoading] = useState(Boolean(point));
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const onGeometryRef = useRef(onGeometry);
  onGeometryRef.current = onGeometry;
  const lat = point?.lat ?? null;
  const lng = point?.lng ?? null;

  useEffect(() => {
    controllerRef.current?.abort();
    setTable(null);
    setError(null);
    // A new point (or the removal of one) invalidates any geometry drawn for the previous point.
    onGeometryRef.current?.(null);
    if (lat === null || lng === null) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    controllerRef.current = controller;
    setLoading(true);
    getUseTable({ lat, lng }, { signal: controller.signal })
      .then(result => {
        if (controller.signal.aborted) return;
        setTable(result);
        void publishParcelGeometry(result, controller.signal, onGeometryRef.current);
      })
      .catch((cause: unknown) => {
        const message = useTableErrorMessage(cause);
        if (!controller.signal.aborted && message) setError(message);
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [lat, lng]);

  const source = table?.source ?? OFFICIAL_USE_TABLE_SOURCE;

  return (
    <section className="use-table" aria-labelledby="use-table-title">
      <div className="section-heading">
        <div>
          <h2 id="use-table-title">Cuadro de usos</h2>
          <p>Mixtura de usos y rubros oficiales de la Ciudad de Buenos Aires.</p>
        </div>
      </div>
      {lat === null && (
        <p className="small-note" role="status">
          Sin un punto de consulta no podemos buscar la parcela en el Cuadro de Usos.
        </p>
      )}
      {lat !== null && loading && <p className="small-note" role="status">Consultando el cuadro de usos oficial…</p>}
      {lat !== null && error && <UseTableError message={error} />}
      {lat !== null && table && !loading && !error && (
        useTableIsEmpty(table)
          ? <UseTableEmptyState limitations={table.limitations} />
          : <UseTableResult data={table} />
      )}
      <p className="hint use-table__disclaimer">{DISCLAIMER}</p>
      <p className="small-note use-table__source">
        Fuente: <a href={source.url} target="_blank" rel="noreferrer">{source.title} <span aria-hidden="true">↗</span></a>
        {" "}— {source.publisher}.
      </p>
    </section>
  );
}
