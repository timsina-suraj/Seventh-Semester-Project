import { useEffect, useState } from "react";

// Returns a copy of `value` that only updates `delayMs` after the last
// change — pair with a `useEffect([debounced])` to fire a search request
// only once the user pauses typing, instead of on every keystroke.
export default function useDebouncedValue(value, delayMs = 300) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(handle);
  }, [value, delayMs]);

  return debounced;
}
