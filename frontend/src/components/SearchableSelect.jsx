import { useEffect, useRef, useState } from "react";

/**
 * A text input that filters a fixed list of options as you type, for fields
 * where free text would let a typo silently pass validation (e.g. district
 * names the backend checks against a fixed whitelist). Mimics a native
 * <input>'s onChange shape ({ target: { name, value } }) so it drops into
 * the same handleChange(e) handlers the rest of the form already uses.
 */
export default function SearchableSelect({
  name,
  value,
  onChange,
  options,
  placeholder = "Type to search...",
  required = false,
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [highlight, setHighlight] = useState(0);
  const rootRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(e) {
      if (rootRef.current && !rootRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = open
    ? options.filter((o) => o.toLowerCase().includes(query.toLowerCase()))
    : [];

  const commit = (option) => {
    onChange({ target: { name, value: option } });
    setOpen(false);
    setQuery("");
  };

  const handleFocus = () => {
    setOpen(true);
    setQuery("");
    setHighlight(0);
  };

  const handleKeyDown = (e) => {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, filtered.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filtered[highlight]) commit(filtered[highlight]);
    } else if (e.key === "Escape") {
      setOpen(false);
      setQuery("");
    }
  };

  return (
    <div className="searchable-select" ref={rootRef}>
      <input
        type="text"
        value={open ? query : value || ""}
        onChange={(e) => {
          setQuery(e.target.value);
          setHighlight(0);
        }}
        onFocus={handleFocus}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        required={required}
        autoComplete="off"
      />
      {open && (
        <ul className="searchable-select-list">
          {filtered.length === 0 && <li className="searchable-select-empty">No matches</li>}
          {filtered.map((option, i) => (
            <li
              key={option}
              className={i === highlight ? "active" : undefined}
              onMouseDown={(e) => {
                // mousedown (not click) so this fires before the input's blur/outside-click handler
                e.preventDefault();
                commit(option);
              }}
              onMouseEnter={() => setHighlight(i)}
            >
              {option}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
