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
  /** Curated activity picked from the suggestions; null when the person kept free text. */
  activitySlug?: string | null;
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

/** Official source cited by the guidance endpoints (RN-05). */
export type OfficialSource = { name: string; url: string; license: string };

/** Activity suggested by GET /guidance/activities (snake_case, as the backend sends it). */
export type ActivitySuggestion = {
  slug: string;
  name: string;
  matched_alias: string;
  similarity: number;
};

export type ActivitySuggestionsResponse = { activities: ActivitySuggestion[] };

export type OfficialProcedure = {
  id: string;
  title: string;
  official_url: string;
  summary: string;
  last_updated: string;
};

/** Official procedure page that publishes a requirement (S3/S4). */
export type RequirementOrigin = {
  procedure_id: string;
  procedure_title: string;
  official_url: string;
};

/** Requirement aggregated across all procedures of an activity, deduplicated by normalized text (S3/S4). */
export type Requirement = {
  id: string;
  text: string;
  heading: string | null;
  origins: RequirementOrigin[];
};

/** Context answers keyed by question id; a missing key means "not answered". */
export type ContextAnswers = Record<string, boolean>;

export type ContextQuestion = {
  id: string;
  text: string;
  answer: boolean | null;
};

/** Procedure discarded by the context answers. */
export type ExcludedProcedure = {
  id: string;
  title: string;
  /** Ids of the context questions whose answer discarded it; missing when the API predates the field. */
  because?: string[];
};

/** Response of GET /guidance/activities/{slug}/procedures. */
export type ActivityProceduresResponse = {
  activity: { slug: string; name: string };
  questions: ContextQuestion[];
  /** `applies`: no conditions or all met; `may_apply`: some condition is still unanswered. */
  procedures: { procedure: OfficialProcedure; note: string; status: 'applies' | 'may_apply' }[];
  excluded_count: number;
  /** Discarded procedures in catalog order; missing when the API predates the field. */
  excluded?: ExcludedProcedure[];
  source: OfficialSource;
  /** Aggregated requirements across all the activity's procedures, independent of context filtering. */
  requirements: Requirement[];
  /** Disclaimer shown verbatim in the requirements panel. */
  requirements_note: string;
};

/** Wire shapes of GET /territory/use-table (snake_case, as the backend sends them). */
export type UseTableRubro = { id: number; name: string };
export type UseTableCategory = { id: number; name: string; rubros: UseTableRubro[] };
export type UseTableResponse = {
  smp: string | null;
  official_address: string | null;
  mix_area: number | null;
  categories: UseTableCategory[];
  source: SourceReference;
  limitations: string[];
};

/** Wire shape of GET /territory/parcel-geometry: real cadastral geometry or null (S12). */
export type ParcelGeometryResponse = {
  geometry: GeoJSON.Geometry | null;
  source: SourceReference;
  limitations: string[];
};

/** Parameters of GET /territory/rubro-referencias, mirroring the query string names. */
export type RubroReferenciasParams = {
  smp: string;
  categoria: number;
  mixtura: number;
  rubro: number;
};

/** Wire shape of GET /territory/rubro-referencias (snake_case, as the backend sends it). */
export type RubroReferencias = {
  permitido_mixtura_de_usos: string[];
  bicicletas: string[];
  estacionamientos: string[];
  cargaydescarga: string[];
  observaciones: string | null;
  source: SourceReference;
  limitations: string[];
};
