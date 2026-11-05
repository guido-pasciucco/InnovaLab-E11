import { useEffect, useId, useState, type KeyboardEvent } from "react";
import { ApiError, searchAddresses } from "../api/client";
import type { Address } from "../types";

const MIN_CHARS = 3;
const DEBOUNCE_MS = 300;
// "Sara Beatriz Fernandez 580" → street "Sara Beatriz Fernandez", number 580.
const TRAILING_NUMBER = /^(.*\D)\s+(\d+)\s*$/;

type Status = "idle" | "loading" | "ready" | "empty" | "error";
type Suggestion = { address: Address; note: string | null };

type Props = {
  id: string;
  value: string;
  selected: Address | null;
  invalid: boolean;
  onChange: (value: string) => void;
  onSelect: (address: Address | null) => void;
  /** Tells the form whether the search service answered, so it can accept free text when it is down. */
  onAvailabilityChange: (available: boolean) => void;
};

/** Text shown in the input: street and number only, so editing it and searching again still works. */
export function inputLabel(address: Address): string {
  if (!address.street) return address.full_address;
  return address.number === null ? address.street : `${address.street} ${address.number}`;
}

function streetKey(address: Address): string {
  return `${address.street}|${address.department}`;
}

/**
 * Georef returns one entry per street segment when there is no number; showing them all looks like
 * duplicates, so they collapse into one suggestion per street and department.
 */
function toSuggestions(addresses: Address[]): Suggestion[] {
  const seen = new Set<string>();
  const suggestions: Suggestion[] = [];
  for (const address of addresses) {
    if (address.number !== null) {
      suggestions.push({ address, note: null });
      continue;
    }
    if (seen.has(streetKey(address))) continue;
    seen.add(streetKey(address));
    suggestions.push({ address, note: "agregá la altura para ubicarla con precisión" });
  }
  return suggestions;
}

/**
 * Some streets have no numbering in Georef (height range 0–0), so "street + number" finds nothing.
 * The street alone still exists: keep the number the person typed and use the street's location.
 * /direcciones does not expose height ranges, so an out-of-range number lands here too; the note
 * is worded to be true in both cases.
 */
function withoutNumbering(addresses: Address[], number: number): Suggestion[] {
  const seen = new Set<string>();
  const suggestions: Suggestion[] = [];
  for (const street of addresses) {
    if (!street.street || seen.has(streetKey(street))) continue;
    seen.add(streetKey(street));
    const place = [street.department, street.province].filter(Boolean).join(", ");
    suggestions.push({
      address: { ...street, number, full_address: `${street.street} ${number}${place ? `, ${place}` : ""}` },
      note: "no encontramos esa altura: ubicación aproximada de la calle",
    });
  }
  return suggestions;
}

async function findSuggestions(query: string, signal: AbortSignal): Promise<Suggestion[]> {
  const { addresses } = await searchAddresses(query, { signal });
  if (addresses.length) return toSuggestions(addresses);
  const match = TRAILING_NUMBER.exec(query);
  if (!match) return [];
  const street = await searchAddresses(match[1].trim(), { signal });
  return withoutNumbering(street.addresses, Number(match[2]));
}

export default function AddressAutocomplete({ id, value, selected, invalid, onChange, onSelect, onAvailabilityChange }: Props) {
  const listId = useId();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  useEffect(() => {
    const query = value.trim();
    if (selected && value === inputLabel(selected)) return;
    if (query.length < MIN_CHARS) {
      setSuggestions([]);
      setStatus("idle");
      setOpen(false);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setStatus("loading");
      setOpen(true);
      try {
        const found = await findSuggestions(query, controller.signal);
        setSuggestions(found);
        setActiveIndex(-1);
        setStatus(found.length ? "ready" : "empty");
        onAvailabilityChange(true);
      } catch (err) {
        if (controller.signal.aborted) return;
        setSuggestions([]);
        setStatus("error");
        setErrorMessage(err instanceof ApiError && err.status === 502
          ? "El servicio de direcciones no está disponible. Podés continuar con la dirección escrita."
          : "No pudimos buscar direcciones. Podés continuar con la dirección escrita.");
        onAvailabilityChange(false);
      }
    }, DEBOUNCE_MS);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [value, selected, onAvailabilityChange]);

  function choose(address: Address) {
    onSelect(address);
    onChange(inputLabel(address));
    setOpen(false);
    setActiveIndex(-1);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!open || !suggestions.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex(index => (index + 1) % suggestions.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex(index => (index <= 0 ? suggestions.length - 1 : index - 1));
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      choose(suggestions[activeIndex].address);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  const showList = open && status !== "idle";
  const activeId = activeIndex >= 0 ? `${listId}-option-${activeIndex}` : undefined;

  return (
    <div className="address-autocomplete">
      <input id={id} name="address" value={value} role="combobox" aria-autocomplete="list" aria-expanded={showList}
        aria-controls={listId} aria-activedescendant={activeId} aria-invalid={invalid}
        onChange={e => { onChange(e.target.value); if (selected) onSelect(null); }}
        onKeyDown={handleKeyDown}
        onFocus={() => { if (suggestions.length && !selected) setOpen(true); }}
        onBlur={() => setOpen(false)}
        placeholder="Ej.: Corrientes 2500" maxLength={200} autoComplete="off" />
      {showList && (
        <ul className="address-suggestions" id={listId} role="listbox">
          {status === "loading" && <li className="address-suggestions__status">Buscando direcciones…</li>}
          {status === "empty" && <li className="address-suggestions__status">No encontramos esa dirección. Revisá la calle y la altura.</li>}
          {status === "error" && <li className="address-suggestions__status address-suggestions__status--error">{errorMessage}</li>}
          {status === "ready" && suggestions.map(({ address, note }, index) => (
            <li key={`${address.full_address}-${index}`} id={`${listId}-option-${index}`} role="option"
              aria-selected={index === activeIndex}
              className={`address-suggestion ${index === activeIndex ? "is-active" : ""}`}
              onMouseDown={e => e.preventDefault()} onClick={() => choose(address)}
              onMouseEnter={() => setActiveIndex(index)}>
              <strong>{inputLabel(address)}</strong>
              <span>{[address.department, address.province, note].filter(Boolean).join(" · ")}
                {address.coordinates === null && " · sin ubicación en el mapa"}</span>
            </li>
          ))}
        </ul>
      )}
      {status === "error" && !showList && <span className="field-hint field-hint--warning">{errorMessage}</span>}
    </div>
  );
}
