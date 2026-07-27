export const capabilityStatuses = [
  "informational",
  "implemented_reference",
  "foundation_available",
  "prototype",
  "specified",
  "planned",
  "not_activated",
  "legally_blocked",
  "production_blocked",
] as const;

export type CapabilityStatus = (typeof capabilityStatuses)[number];

export const statusLabels: Record<CapabilityStatus, string> = {
  informational: "Information",
  implemented_reference: "Referenz implementiert",
  foundation_available: "Technische Grundlage vorhanden",
  prototype: "Öffentlicher Prototyp",
  specified: "Spezifiziert",
  planned: "Geplant",
  not_activated: "Nicht aktiviert",
  legally_blocked: "Rechtliche Freigabe ausstehend",
  production_blocked: "Produktionsfreigabe ausstehend",
};
