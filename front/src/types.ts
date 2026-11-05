export type GeoPoint = { lat: number; lng: number };

export type SourceReference = {
  id: string;
  title: string;
  publisher: string;
  url: string;
  retrievedAt?: string;
  note?: string;
};

export type GuidanceStep = {
  id: string;
  title: string;
  description: string;
  documents?: string[];
  sourceIds: string[];
};

export type TerritorialFeature = {
  id: string;
  label: string;
  description: string;
  geometry: GeoJSON.Geometry;
};

export type ConsultationRequest = {
  activity: string;
  address: string;
  /** Coordinates of the address picked from the suggestions; null when unknown. */
  point?: GeoPoint | null;
};

export type ConsultationResponse = {
  consultationId: string;
  interpretedActivity: string;
  normalizedAddress: string;
  point: GeoPoint | null;
  summary: string;
  steps: GuidanceStep[];
  territorialFeatures: TerritorialFeature[];
  sources: SourceReference[];
  limitations: string[];
};

export type FollowUpRequest = { question: string };
export type FollowUpResponse = {
  answer: string;
  sourceIds: string[];
  limitations?: string[];
};

/** Address returned by GET /geolocation/addresses (snake_case, as the backend sends it). */
export type Address = {
  full_address: string;
  street: string | null;
  number: number | null;
  department: string | null;
  locality: string | null;
  province: string | null;
  coordinates: { latitude: number; longitude: number } | null;
};

export type AddressSearchResponse = { addresses: Address[] };
