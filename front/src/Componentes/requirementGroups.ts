import type { Requirement } from "../types";

export const SHARED_GROUP_ID = "shared";
const OTHER_GROUP_ID = "other";

export type RequirementGroup = {
  /** Procedure id, or a fixed id for the shared and "other" groups. */
  id: string;
  title: string;
  /** Official page of the procedure; absent for the shared and "other" groups. */
  url?: string;
  items: Requirement[];
};

/**
 * Groups the aggregated requirements so each one appears once: those asked by
 * several procedures go to a shared group first, the rest under the only
 * procedure that asks for them, following the order of the procedures list.
 */
export function groupRequirements(
  requirements: Requirement[],
  procedures: { id: string; title: string }[],
): RequirementGroup[] {
  const shared: RequirementGroup = { id: SHARED_GROUP_ID, title: "Sirve para varios trámites", items: [] };
  const other: RequirementGroup = { id: OTHER_GROUP_ID, title: "Otros requisitos", items: [] };
  const byProcedure = new Map<string, RequirementGroup>(
    procedures.map(({ id, title }) => [id, { id, title, items: [] }]),
  );

  for (const raw of requirements) {
    // The API may list the same procedure twice for one requirement; it still counts once.
    const origins = raw.origins.filter((origin, index, all) =>
      all.findIndex(other => other.procedure_id === origin.procedure_id) === index);
    const requirement = origins.length === raw.origins.length ? raw : { ...raw, origins };
    if (origins.length > 1) shared.items.push(requirement);
    else if (origins.length === 0) other.items.push(requirement);
    else {
      const [origin] = origins;
      const group = byProcedure.get(origin.procedure_id)
        ?? { id: origin.procedure_id, title: origin.procedure_title, items: [] };
      group.url ??= origin.official_url;
      group.items.push(requirement);
      byProcedure.set(origin.procedure_id, group);
    }
  }

  return [shared, ...byProcedure.values(), other].filter(group => group.items.length > 0);
}

/** How many requirements a procedure asks for, counting those it shares with others. */
export function requirementCount(requirements: Requirement[], procedureId: string): number {
  return requirements.filter(({ origins }) => origins.some(origin => origin.procedure_id === procedureId)).length;
}
