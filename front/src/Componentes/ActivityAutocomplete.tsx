import { useEffect, useId, useState, type KeyboardEvent } from "react";
import { suggestActivities } from "../api/client";
import { describeError } from "../api/errors";
import type { ActivitySuggestion } from "../types";
import { TEXT_RULES, reachesThreshold } from "../validation";

const DEBOUNCE_MS = 300;

type Status = "idle" | "loading" | "ready" | "empty" | "error";

type Props = {
  id: string;
  value: string;
  selected: ActivitySuggestion | null;
  invalid: boolean;
  /** Ids of the hint, counter and error that describe the field. */
  describedBy?: string;
  onChange: (value: string) => void;
  onSelect: (activity: ActivitySuggestion | null) => void;
};

/**
 * Suggests curated activities that mean the same as the typed text ("barbería" → Peluquería).
 * Picking one is optional: the catalog is small, so free text still works and keeps the generic guidance.
 * It reuses the address autocomplete styles so both fields look and behave the same.
 */
export default function ActivityAutocomplete({ id, value, selected, invalid, describedBy, onChange, onSelect }: Props) {
  const listId = useId();
  const [suggestions, setSuggestions] = useState<ActivitySuggestion[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  useEffect(() => {
    const query = value.trim();
    if (selected && value === selected.name) return;
    // Below the API's threshold there is nothing to ask: no request is sent.
    if (!reachesThreshold(query, TEXT_RULES.activity)) {
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
        const { activities } = await suggestActivities(query, { signal: controller.signal });
        setSuggestions(activities);
        setActiveIndex(-1);
        setStatus(activities.length ? "ready" : "empty");
      } catch (err) {
        const message = describeError(err);
        if (controller.signal.aborted || message === null) return;
        setSuggestions([]);
        setStatus("error");
        setErrorMessage(`${message} Podés continuar con la actividad escrita.`);
      }
    }, DEBOUNCE_MS);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [value, selected]);

  function choose(activity: ActivitySuggestion) {
    onSelect(activity);
    onChange(activity.name);
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
      choose(suggestions[activeIndex]);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  const showList = open && status !== "idle";
  const activeId = activeIndex >= 0 ? `${listId}-option-${activeIndex}` : undefined;

  return (
    <div className="address-autocomplete">
      <input id={id} name="activity" value={value} role="combobox" aria-autocomplete="list" aria-expanded={showList}
        aria-controls={listId} aria-activedescendant={activeId} aria-invalid={invalid} aria-describedby={describedBy}
        onChange={e => { onChange(e.target.value); if (selected) onSelect(null); }}
        onKeyDown={handleKeyDown}
        onFocus={() => { if (suggestions.length && !selected) setOpen(true); }}
        onBlur={() => setOpen(false)}
        placeholder="Ej.: abrir una cafetería" maxLength={TEXT_RULES.activity.max} autoComplete="off" />
      {showList && (
        <ul className="address-suggestions" id={listId} role="listbox">
          {status === "loading" && <li className="address-suggestions__status">Buscando actividades…</li>}
          {status === "empty" && <li className="address-suggestions__status">No encontramos una actividad parecida. Podés continuar con lo que escribiste.</li>}
          {status === "error" && <li className="address-suggestions__status address-suggestions__status--error">{errorMessage}</li>}
          {status === "ready" && suggestions.map((activity, index) => (
            <li key={activity.slug} id={`${listId}-option-${index}`} role="option"
              aria-selected={index === activeIndex}
              className={`address-suggestion ${index === activeIndex ? "is-active" : ""}`}
              onMouseDown={e => e.preventDefault()} onClick={() => choose(activity)}
              onMouseEnter={() => setActiveIndex(index)}>
              <strong>{activity.name}</strong>
              {activity.matched_alias !== activity.name && <span>parecido a «{activity.matched_alias}»</span>}
            </li>
          ))}
        </ul>
      )}
      {status === "error" && !showList && <span className="field-hint field-hint--warning">{errorMessage}</span>}
    </div>
  );
}
