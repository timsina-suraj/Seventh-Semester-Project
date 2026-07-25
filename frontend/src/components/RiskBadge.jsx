const RISK_CLASS = {
  Low: "risk-low",
  Medium: "risk-medium",
  High: "risk-high",
  "Very High": "risk-very-high",
};

export default function RiskBadge({ level }) {
  const cls = RISK_CLASS[level] || "risk-low";
  return <span className={`badge ${cls}`}>{level}</span>;
}
