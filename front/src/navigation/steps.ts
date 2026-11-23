export type Step = 1 | 2 | 3 | 4 | 5;

/** The five steps of a consultation, each with its own address so it can be shared, reloaded and reached with Back. */
export const STEPS: readonly { step: Step; label: string; path: string }[] = [
  { step: 1, label: "Consulta", path: "/consulta" },
  { step: 2, label: "Análisis", path: "/analisis" },
  { step: 3, label: "Orientación", path: "/orientacion" },
  { step: 4, label: "Mapa", path: "/mapa" },
  { step: 5, label: "Asistente", path: "/asistente" },
];

export const HOME_PATH = STEPS[0].path;

export function pathOf(step: Step): string {
  return STEPS[step - 1].path;
}

export function stepFromPath(pathname: string): Step | null {
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, "") : pathname;
  return STEPS.find(item => item.path === path)?.step ?? null;
}

export type StepState = {
  /** A consultation is being processed right now. */
  analyzing: boolean;
  /** There is a consultation result to show. */
  hasResult: boolean;
};

/** A step can be opened only when it has something to show; the others stay visible but disabled. */
export function isStepAvailable(step: Step, { analyzing, hasResult }: StepState): boolean {
  if (step === 1) return true;
  if (step === 2) return analyzing || hasResult;
  return hasResult;
}
