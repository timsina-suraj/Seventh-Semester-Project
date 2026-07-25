import { useEffect, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, ComposedChart, Legend,
  Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip,
  XAxis, YAxis,
} from "recharts";
import * as api from "../../api/endpoints";

const PIE_COLORS = ["#dc2626", "#16a34a"];

const cmCell = (val, bg, label, cmTotal) => (
  <div style={{
    background: bg, borderRadius: 8, padding: "18px 10px",
    textAlign: "center", flex: 1,
  }}>
    <div style={{ fontSize: 28, fontWeight: 800, color: "#fff" }}>{val}</div>
    <div style={{ fontSize: 11, color: "rgba(255,255,255,0.8)", marginTop: 4 }}>{label}</div>
    <div style={{ fontSize: 12, color: "rgba(255,255,255,0.7)" }}>
      {((val / cmTotal) * 100).toFixed(1)}%
    </div>
  </div>
);

const CardTitle = ({ children }) => (
  <div className="section-title" style={{ margin: "0 0 16px" }}>{children}</div>
);

export default function Analytics() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getAnalytics()
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.detail || "Could not load analytics."));
  }, []);

  if (error) {
    return (
      <div>
        <div className="page-header">
          <h1>Analytics</h1>
        </div>
        <div className="error-text" style={{ padding: 20 }}>{error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div>
        <div className="page-header">
          <h1>Analytics</h1>
        </div>
        <div style={{ padding: 20 }}>Loading analytics data from trained models...</div>
      </div>
    );
  }

  const {
    actualVsPredicted,
    modelRegressionData,
    classificationData,
    CM,
    diagnosisDist,
    symptomsData,
    weatherData,
  } = data;

  const cmTotal = CM ? CM.TP + CM.FP + CM.FN + CM.TN : 0;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Analytics</h1>
        </div>
      </div>

      <div className="grid-2">

        {/* 1. Actual vs Predicted Cases */}
        <div className="card">
          <CardTitle>📈 Actual vs Predicted Cases</CardTitle>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={actualVsPredicted}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="Actual"    stroke="#2563eb" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="Predicted" stroke="#dc2626" strokeWidth={2} strokeDasharray="5 4" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 2. Dengue Trend Over Time */}
        <div className="card">
          <CardTitle>📉 Dengue Trend Over Time (Monthly)</CardTitle>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={actualVsPredicted}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" fontSize={12} />
              <YAxis fontSize={12} />
              <Tooltip />
              <Line type="monotone" dataKey="Actual" name="Cases" stroke="#7c3aed" strokeWidth={2.5} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
      
        {/* 3. Model Performance (RMSE, MAE) */}
        <div className="card">
          <CardTitle>📊 Model Performance — RMSE &amp; MAE</CardTitle>
          <ResponsiveContainer width="100%" height={360}>
            <BarChart layout="vertical" data={modelRegressionData} barGap={2} margin={{ top: 20, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" xAxisId="top" orientation="top" fontSize={11} />
              <XAxis type="number" xAxisId="bottom" orientation="bottom" domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} fontSize={11} />
              <YAxis type="category" dataKey="model" fontSize={11} width={80} />
              <Tooltip />
              <Legend />
              <Bar xAxisId="top" dataKey="RMSE" fill="#dc2626" radius={[0,4,4,0]} />
              <Bar xAxisId="top" dataKey="MAE"  fill="#d97706" radius={[0,4,4,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

      {/* 4. Model Performance (R²) */}
      <div className="card">
        <CardTitle>📈 Model Performance — R² Score Comparison</CardTitle>

          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={modelRegressionData}>
              <CartesianGrid strokeDasharray="3 3" />

              <XAxis
                dataKey="model"
                fontSize={11}
              />

              <YAxis
                domain={["auto", "auto"]}
                tickFormatter={(v)=>v.toFixed(2)}
              />

              <Tooltip />

              <Bar
                dataKey="R² Score"
                fill="#2563eb"
                barSize={40}
                radius={[6,6,0,0]}
              />

            </BarChart>
          </ResponsiveContainer>
         </div>


        {/* 5. Confusion Matrix */}
        <div className="card">
          <CardTitle>🔲 Confusion Matrix</CardTitle>
          {CM ? (
            <>
              <div style={{ marginBottom: 10, fontSize: 12, color: "var(--color-text-muted)" }}>
                <strong>Positive class = Dengue Positive</strong>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "auto 1fr 1fr", gap: 6, alignItems: "center" }}>
                {/* header row */}
                <div />
                <div style={{ textAlign: "center", fontWeight: 700, fontSize: 12, color: "var(--color-text-muted)" }}>Predicted Positive</div>
                <div style={{ textAlign: "center", fontWeight: 700, fontSize: 12, color: "var(--color-text-muted)" }}>Predicted Negative</div>
                {/* row 1 */}
                <div style={{ fontWeight: 700, fontSize: 12, color: "var(--color-text-muted)", writingMode: "vertical-rl", textOrientation: "mixed", transform: "rotate(180deg)", paddingRight: 6 }}>Actual Positive</div>
                {cmCell(CM.TP, "#16a34a", "True Positive", cmTotal)}
                {cmCell(CM.FN, "#dc2626", "False Negative", cmTotal)}
                {/* row 2 */}
                <div style={{ fontWeight: 700, fontSize: 12, color: "var(--color-text-muted)", writingMode: "vertical-rl", textOrientation: "mixed", transform: "rotate(180deg)", paddingRight: 6 }}>Actual Negative</div>
                {cmCell(CM.FP, "#d97706", "False Positive", cmTotal)}
                {cmCell(CM.TN, "#2563eb", "True Negative", cmTotal)}
              </div>
            </>
          ) : (
             <div className="empty-state">No confusion matrix data available.</div>
          )}
        </div>

        {/* 6. Classification Comparison */}
        <div className="card">
          <CardTitle>🏆 Classification Comparison (Accuracy, Precision, Recall, F1)</CardTitle>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={classificationData} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="model" fontSize={11} />
              <YAxis domain={[0, 1]} tickFormatter={(v) => `${(v*100).toFixed(0)}%`} fontSize={11} />
              <Tooltip formatter={(v) => `${(v*100).toFixed(1)}%`} />
              <Legend />
              <Bar dataKey="Accuracy"  fill="#2563eb" radius={[4,4,0,0]} />
              <Bar dataKey="Precision" fill="#16a34a" radius={[4,4,0,0]} />
              <Bar dataKey="Recall"    fill="#d97706" radius={[4,4,0,0]} />
              <Bar dataKey="F1"        fill="#7c3aed" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 7. Dengue Positive/Negative Distribution */}
        <div className="card">
          <CardTitle>🥧 Dengue Positive / Negative Distribution</CardTitle>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={diagnosisDist}
                cx="50%"
                cy="50%"
                outerRadius={90}
                dataKey="value"
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                labelLine={false}
              >
                {diagnosisDist.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v, name) => [v, name]} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 8. Symptoms Frequency */}
        <div className="card">
          <CardTitle>🤒 Symptoms Frequency</CardTitle>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={symptomsData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" fontSize={12} />
              <YAxis type="category" dataKey="symptom" fontSize={12} width={100} />
              <Tooltip />
              <Bar dataKey="count" name="Patients" fill="#0891b2" radius={[0,4,4,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* 9. Weather vs Dengue Cases */}
        <div className="card" style={{ gridColumn: "1 / -1" }}>
          <CardTitle>🌦️ Weather vs Dengue Cases</CardTitle>
          <ResponsiveContainer width="100%" height={280}>
            <ComposedChart data={weatherData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" fontSize={12} />
              <YAxis yAxisId="left"  fontSize={12} label={{ value: "Cases / Rainfall (mm)", angle: -90, position: "insideLeft", fontSize: 11, dy: 60 }} />
              <YAxis yAxisId="right" orientation="right" fontSize={12} label={{ value: "Temp (°C)", angle: 90, position: "insideRight", fontSize: 11, dy: -30 }} />
              <Tooltip />
              <Legend />
              <Bar     yAxisId="left"  dataKey="Rainfall" name="Rainfall (mm)" fill="#93c5fd" radius={[4,4,0,0]} />
              <Line    yAxisId="left"  type="monotone" dataKey="Cases" name="Dengue Cases" stroke="#dc2626" strokeWidth={2.5} dot={{ r: 3 }} />
              <Line    yAxisId="right" type="monotone" dataKey="Temp"  name="Temp (°C)"   stroke="#f59e0b" strokeWidth={2} strokeDasharray="5 3" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
}
