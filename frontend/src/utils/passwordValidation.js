// Mirrors _validate_password_strength in backend/app/schemas/auth.py — keep
// both in sync. Client-side check exists only to give the user a faster,
// friendlier error than a round trip to the API; the backend re-checks
// every rule below regardless of what the client sends.

export const PASSWORD_RULES_HINT =
  "At least 8 characters, with a lowercase letter, an uppercase letter, a digit, and a special character.";

function joinRequirements(items) {
  if (items.length === 1) return items[0];
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(", ")}, and ${items[items.length - 1]}`;
}

/** Returns an error message string if the password fails a rule, or null if it's valid. */
export function validatePasswordStrength(password) {
  const missing = [];
  if (password.length < 8) missing.push("at least 8 characters");
  if (!/[a-z]/.test(password)) missing.push("a lowercase letter");
  if (!/[A-Z]/.test(password)) missing.push("an uppercase letter");
  if (!/[0-9]/.test(password)) missing.push("a digit");
  if (!/[^A-Za-z0-9]/.test(password)) missing.push("a special character");

  if (missing.length === 0) return null;
  return `Password must contain ${joinRequirements(missing)}.`;
}
