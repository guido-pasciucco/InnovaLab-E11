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
};

export type ConsultationResponse = {
  consultationId: string;
  interpretedActivity: string;
  normalizedAddress: string;
  point: GeoPoint;
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
