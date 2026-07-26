export default function Modal({ title, onClose, children, maxWidth = 480 }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed", inset: 0, background: "rgba(15, 23, 42, 0.55)",
        display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, padding: 16,
      }}
    >
      <div
        className="card"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth, width: "100%", maxHeight: "85vh", overflowY: "auto" }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div className="section-title" style={{ margin: 0 }}>{title}</div>
          <button className="btn secondary" onClick={onClose} style={{ padding: "4px 10px" }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}
