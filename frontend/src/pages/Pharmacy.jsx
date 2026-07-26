import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/endpoints";
import { useAuth } from "../auth/AuthContext.jsx";
import useDebouncedValue from "../hooks/useDebouncedValue.js";

export default function Pharmacy() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const canManage = user.role === "admin" || user.role === "receptionist";
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search);

  const load = () => api.listPharmacyItems(undefined, debouncedSearch || undefined).then((res) => setItems(res.data));

  useEffect(() => {
    load();
  }, [debouncedSearch]);

  const adjustStock = async (item, delta) => {
    await api.updatePharmacyItem(item.id, {
      stock_quantity: Math.max(0, item.stock_quantity + delta),
    });
    load();
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Pharmacy Inventory</h1>
        </div>
        {canManage && (
          <button className="btn" onClick={() => navigate("/pharmacy/add")}>
            + Add Item
          </button>
        )}
      </div>

      <div className="card">
        <div className="page-header" style={{ marginBottom: 12 }}>
          <div className="section-title" style={{ margin: 0 }}>Inventory ({items.length})</div>
          <input
            type="text"
            placeholder="Search by medicine name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ maxWidth: 260 }}
          />
        </div>
        <table>
          <thead>
            <tr>
              <th>Item</th>
              <th>Stock</th>
              <th>Unit</th>
              <th>Reorder at</th>
              {canManage && <th>Adjust stock</th>}
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>
                  {item.name}
                  {item.is_low_stock && (
                    <span className="badge risk-high" style={{ marginLeft: 8 }}>
                      Low stock
                    </span>
                  )}
                </td>
                <td>{item.stock_quantity}</td>
                <td>{item.unit}</td>
                <td>{item.reorder_threshold}</td>
                {canManage && (
                  <td style={{ display: "flex", gap: 6 }}>
                    <button className="btn secondary" onClick={() => adjustStock(item, -10)}>
                      −10
                    </button>
                    <button className="btn secondary" onClick={() => adjustStock(item, 10)}>
                      +10
                    </button>
                  </td>
                )}
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={canManage ? 5 : 4} className="empty-state">
                  No items in inventory yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
