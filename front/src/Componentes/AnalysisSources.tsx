import { useEffect, useState } from "react";

// Simulated source polling while the consultation request is in flight.
// The real sources depend on the backend integrations; this is a progress
// indicator, not a claim about which sources were actually queried.
const SOURCES: [string, number][] = [
  ["Trámites y requisitos", 1100],
  ["Zonificación y usos del suelo", 1300],
  ["Habilitaciones y control", 1200],
  ["Cartografía y capas territoriales", 1500],
  ["Datos abiertos de la Ciudad", 1000],
];

export default function AnalysisSources({ running }: { running: boolean }) {
  // -1 = not started · i = consulting source i · SOURCES.length = all done
  const [step, setStep] = useState(-1);

  useEffect(() => {
    if (!running) return;
    if (step >= SOURCES.length) return;
    const delay = step < 0 ? 30 : SOURCES[step][1];
    const timer = setTimeout(() => setStep((current) => current + 1), delay);
    return () => clearTimeout(timer);
  }, [running, step]);

  return (
    <div className="analysis-sources" aria-live="polite">
      <h2>Consultando fuentes oficiales</h2>
      {SOURCES.map(([name, ms], index) => {
        const done = index < step;
        const state = done ? "Listo" : index === step ? "Consultando…" : "En espera";
        return (
          <div className="analysis-source" key={name}>
            <div className="analysis-source__head">
              <span>{name}</span>
              <span className={`analysis-source__state${done ? " is-done" : ""}`}>{state}</span>
            </div>
            <div className="analysis-source__bar">
              <span
                style={{
                  width: index <= step ? "100%" : "0",
                  transition: `width ${ms}ms linear`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
