import { useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../../api/endpoints";

const EMPTY_FORM = { name: "", unit: "units", stock_quantity: 0, reorder_threshold: 20 };

export default function AddPharmacyItem() {
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.createPharmacyItem({
        ...form,
        stock_quantity: Number(form.stock_quantity),
        reorder_threshold: Number(form.reorder_threshold),
      });
      navigate("/pharmacy");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not add item.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Add Pharmacy Item</h1>
        </div>
        <button className="btn secondary" onClick={() => navigate("/pharmacy")}>
          ← View Inventory
        </button>
      </div>

      <div className="card" style={{ maxWidth: 560 }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Item name</label>
            <input name="name" value={form.name} onChange={handleChange} required />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Unit</label>
              <input name="unit" value={form.unit} onChange={handleChange} placeholder="e.g. tablets, ml" />
            </div>
            <div className="form-group">
              <label>Stock quantity</label>
              <input
                type="number"
                name="stock_quantity"
                min={0}
                value={form.stock_quantity}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label>Reorder threshold</label>
              <input
                type="number"
                name="reorder_threshold"
                min={0}
                value={form.reorder_threshold}
                onChange={handleChange}
              />
            </div>
          </div>
          {error && <div className="error-text">{error}</div>}
          <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
            <button className="btn" type="submit" disabled={saving}>
              {saving ? "Saving..." : "Add item"}
            </button>
            <button className="btn secondary" type="button" onClick={() => navigate("/pharmacy")}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
