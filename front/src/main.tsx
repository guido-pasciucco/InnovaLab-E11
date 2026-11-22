import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "leaflet/dist/leaflet.css";
import "./style.css";
import App from "./App";
import ErrorBoundary from "./Componentes/ErrorBoundary";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ErrorBoundary variant="screen">
      <App />
    </ErrorBoundary>
  </StrictMode>
);