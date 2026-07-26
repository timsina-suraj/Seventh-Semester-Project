// Resolve a display name for an id against a list of {id, full_name} rows
// (patients, doctors, ...), falling back to "#<id>" when the row hasn't
// loaded yet or doesn't exist.
export function nameById(list, id) {
  return list.find((item) => item.id === id)?.full_name || `#${id}`;
}

// Same lookup, precomputed as an id -> name map — cheaper when resolving
// many ids against the same list (e.g. once per table row).
export function nameMapById(list) {
  return Object.fromEntries(list.map((item) => [item.id, item.full_name]));
}
