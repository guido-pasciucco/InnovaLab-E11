import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { GeoPoint, TerritorialFeature } from '../types';
import { useEffect } from 'react';

// Corregir las rutas de los recursos de los marcadores predeterminados de Leaflet al realizar el empaquetado con Vite.
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
const defaultIcon = L.icon({ iconUrl: markerIcon, iconRetinaUrl: markerIcon2x, shadowUrl: markerShadow,
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41] });
L.Marker.prototype.options.icon = defaultIcon;

function Recenter({ point }: { point: GeoPoint }) {
  const map = useMap();
  useEffect(() => { map.setView([point.lat, point.lng], 16); }, [map, point.lat, point.lng]);
  return null;
}

export default function MapPanel({ point, address, features }: { point: GeoPoint; address: string; features: TerritorialFeature[] }) {
  return <section className="panel map-panel">
    <div className="section-heading"><div><h2>Ubicación y territorio</h2><p>{address}</p></div><span className="badge">Mapa demo</span></div>
    <MapContainer center={[point.lat, point.lng]} zoom={15} scrollWheelZoom className="map">
      <Recenter point={point} />
      <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Marker position={[point.lat, point.lng]}><Popup>{address}</Popup></Marker>
      {features.map(feature => <GeoJSON key={feature.id} data={feature.geometry} />)}
    </MapContainer>
    <p className="hint">La ubicación del marcador en la demo es fija. En producción, el backend debe geocodificar y devolver coordenadas verificadas y capas con procedencia.</p>
  </section>;
