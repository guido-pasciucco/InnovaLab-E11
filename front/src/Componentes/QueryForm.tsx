import { useState, type FormEvent } from "react";
import { geocodeAddressNominatim } from "../api/client";
import ActivityAutocomplete from "./ActivityAutocomplete";
import AddressAutocomplete from "./AddressAutocomplete";
import type { ActivitySuggestion, Address, ConsultationRequest, GeoPoint } from "../types";
import { TEXT_RULES, validateActivity, validateAddress } from "../validation";

type Props = { onSubmit: (value: ConsultationRequest) => void; busy: boolean };

function toGeoPoint(coordinates: Address["coordinates"]): GeoPoint | null {
  return coordinates ? { lat: coordinates.latitude, lng: coordinates.longitude } : null;
}

export default function QueryForm({ onSubmit, busy }: Props) {
  const [activity, setActivity] = useState("");
  const [selectedActivity, setSelectedActivity] = useState<ActivitySuggestion | null>(null);
  const [address, setAddress] = useState("");
  const [selectedAddress, setSelectedAddress] = useState<Address | null>(null);
  const [searchAvailable, setSearchAvailable] = useState(true);
  const [locating, setLocating] = useState(false);
  const [activityError, setActivityError] = useState("");
  const [addressError, setAddressError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    // Validate both fields at once so every problem shows next to its field before anything is sent.
    const activityProblem = validateActivity(activity);
    const addressProblem = validateAddress(address);
    setActivityError(activityProblem ?? "");
    setAddressError(addressProblem ?? "");
    if (activityProblem || addressProblem) return;
    const activitySlug = selectedActivity?.slug ?? null;
    if (selectedAddress) {
      onSubmit({ activity: activity.trim(), address: selectedAddress.full_address, point: toGeoPoint(selectedAddress.coordinates), activitySlug });
      return;
    }
    if (searchAvailable) {
      setAddressError("Elegí una dirección de la lista de sugerencias.");
      return;
    }
    // Free text without backend geocoding: try Nominatim so the map still gets a point.
    setLocating(true);
    try {
      const point = await geocodeAddressNominatim(address.trim());
      onSubmit({ activity: activity.trim(), address: address.trim(), point, activitySlug });
    } finally {
      setLocating(false);
    }
  }

  return (
    <form className="query-form panel" onSubmit={handleSubmit} noValidate>
      <div className="query-field">
        <label htmlFor="activity">¿Qué actividad querés realizar?</label>
        <ActivityAutocomplete id="activity" value={activity} selected={selectedActivity}
          invalid={!!activityError}
          describedBy={["activity-hint", "activity-counter", activityError && "activity-error"].filter(Boolean).join(" ")}
          onChange={value => { setActivity(value); setActivityError(""); }} onSelect={setSelectedActivity} />
        <div className="field-meta">
          <span className="field-hint" id="activity-hint">Elegí una actividad de la lista para ver los trámites oficiales que suelen aplicar.</span>
          <span className="char-counter" id="activity-counter">{activity.length}/{TEXT_RULES.activity.max}</span>
        </div>
        {activityError && <p className="field-error" id="activity-error" role="alert">{activityError}</p>}
      </div>
      <div className="query-field">
        <label htmlFor="address">¿En qué dirección?</label>
        <AddressAutocomplete id="address" value={address} selected={selectedAddress}
          invalid={!!addressError}
          describedBy={["address-hint", addressError && "address-error"].filter(Boolean).join(" ")}
          onChange={value => { setAddress(value); setAddressError(""); }} onSelect={setSelectedAddress}
          onAvailabilityChange={setSearchAvailable} />
        <span className="field-hint" id="address-hint">Escribí calle y altura, sin el barrio, y elegí una opción de la lista. También podés usar «Corrientes y Callao» o «Corrientes entre Callao y Riobamba».</span>
        {addressError && <p className="field-error" id="address-error" role="alert">{addressError}</p>}
      </div>
      <button className="primary query-submit" type="submit" disabled={busy || locating}>{busy ? "Consultando…" : locating ? "Ubicando dirección…" : <>Consultar requisitos <span aria-hidden="true">→</span></>}</button>
      <p className="hint">La orientación es inicial y depende de las fuentes oficiales conectadas.</p>
    </form>
  );
}
