import { useEffect, useState } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const RISK_COLOR = {
  Low: "#16a34a",
  Medium: "#d97706",
  High: "#ea580c",
  "Very High": "#dc2626",
};

const NEPAL_CENTER = [28.3949, 84.124];
const NEPAL_BOUNDS = [
  [26.3, 80.0], // Southwest corner
  [30.5, 88.5], // Northeast corner
];

function Legend() {
  const map = useMap();

  useEffect(() => {
    const legend = L.control({ position: "bottomright" });

    legend.onAdd = function () {
      const div = L.DomUtil.create("div", "info legend");

      div.innerHTML = `
        <div style="
          background:white;
          padding:10px;
          border-radius:8px;
          box-shadow:0 2px 6px rgba(0,0,0,.3);
          font-size:14px;
        ">
          <h4 style="margin:0 0 8px;">Risk Level</h4>

          <div><span style="display:inline-block;width:16px;height:16px;background:#16a34a;margin-right:8px;"></span>Low</div>
          <div><span style="display:inline-block;width:16px;height:16px;background:#d97706;margin-right:8px;"></span>Medium</div>
          <div><span style="display:inline-block;width:16px;height:16px;background:#ea580c;margin-right:8px;"></span>High</div>
          <div><span style="display:inline-block;width:16px;height:16px;background:#dc2626;margin-right:8px;"></span>Very High</div>
          <div><span style="display:inline-block;width:16px;height:16px;background:#d1d5db;margin-right:8px;"></span>N/A</div>
        </div>
      `;

      return div;
    };

    legend.addTo(map);

    return () => {
      legend.remove();
    };
  }, [map]);

  return null;
}

function MapExtras() {
  const map = useMap();

  useEffect(() => {
    // Scale Control (Added first so North Pointer stacks above it)
    const scaleControl = L.control.scale({ position: "bottomleft", metric: true, imperial: false });
    scaleControl.addTo(map);

    // North Pointer
    const northControl = L.control({ position: "bottomleft" });
    northControl.onAdd = function () {
      const div = L.DomUtil.create("div", "leaflet-control");
      div.innerHTML = `
        <div style="background:white; width:40px; height:40px; display:flex; flex-direction:column; align-items:center; justify-content:center; border-radius:4px; box-shadow:0 1px 5px rgba(0,0,0,0.65); font-weight:bold; margin-bottom: 8px;">
          <span style="font-size:16px; line-height:1;">▲</span>
          <span style="font-size:12px; line-height:1;">N</span>
        </div>
      `;
      return div;
    };
    northControl.addTo(map);

    return () => {
      northControl.remove();
      scaleControl.remove();
    };
  }, [map]);

  return null;
}

export default function NepalRiskMap({ points }) {
  const [geoData, setGeoData] = useState(null);

  useEffect(() => {
    fetch("/district.geojson")
      .then((res) => res.json())
      .then((data) => setGeoData(data))
      .catch((err) => console.error("Failed to load GeoJSON:", err));
  }, []);

  const districtMap = {};

  points.forEach((p) => {
    districtMap[p.district.toUpperCase()] = p;
  });

  const style = (feature) => {
    const district =
      feature.properties.DISTRICT;

    const point = districtMap[district];

    return {
      fillColor: point
        ? RISK_COLOR[point.risk_level]
        : "#d1d5db",
      weight: 1,
      opacity: 1,
      color: "#444",
      fillOpacity: 0.75,
    };
  };

  const onEachFeature = (feature, layer) => {
    const district =
      feature.properties.DISTRICT;
      const point = districtMap[district];

    if (point) {
      layer.bindPopup(`
        <div style="min-width:220px">
          <h3 style="margin:0 0 8px 0;">${point.district}</h3>

          <p><strong>Predicted Cases:</strong> ${point.predicted_cases}</p>

          <p><strong>Previous Cases:</strong> ${
            point.previous_cases ?? "N/A"
          }</p>

          <p><strong>Risk Level:</strong> ${point.risk_level}</p>
        </div>
      `);
    } else {
      layer.bindPopup(`
        <strong>${district}</strong><br/>
        No prediction available.
      `);
    }

    layer.on({
      mouseover: (e) => {
        e.target.setStyle({
          weight: 3,
          color: "#000",
          fillOpacity: 0.9,
        });

        e.target.bringToFront();
      },

      mouseout: (e) => {
        e.target.setStyle(style(feature));
      },
    });
  };

  return (
    <MapContainer
      center={NEPAL_CENTER}
      zoom={7}
      scrollWheelZoom={true}
      maxBounds={NEPAL_BOUNDS}
      maxBoundsViscosity={1.0}
      minZoom={7}
      className="leaflet-map-container"
      style={{ height: "600px", width: "100%",background: "#f3f4f6" }}
      >
        
      {/* <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        noWrap={true}
      /> */}
      <Legend/>
      <MapExtras/>
      {geoData && (
        <GeoJSON
          data={geoData}
          style={style}
          onEachFeature={onEachFeature}
        />
      )}
    </MapContainer>
  );
}