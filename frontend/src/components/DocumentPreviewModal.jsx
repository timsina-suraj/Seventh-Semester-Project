import { useEffect, useState } from "react";
import * as api from "../api/endpoints";
import Modal from "./Modal.jsx";

export default function DocumentPreviewModal({ document, onClose }) {
  const [preview, setPreview] = useState(null); // { url, contentType }
  const [error, setError] = useState("");

  useEffect(() => {
    let objectUrl = null;
    api.getDocumentPreviewUrl(document.id)
      .then((result) => {
        objectUrl = result.url;
        setPreview(result);
      })
      .catch(() => setError("Could not load this document for preview."));
    return () => {
      if (objectUrl) window.URL.revokeObjectURL(objectUrl);
    };
  }, [document.id]);

  return (
    <Modal title={document.original_filename} onClose={onClose} maxWidth={800}>
      {error && <div className="error-text">{error}</div>}
      {!error && !preview && <div className="empty-state">Loading preview…</div>}
      {preview && preview.contentType.startsWith("image/") && (
        <img src={preview.url} alt={document.original_filename} style={{ maxWidth: "100%", borderRadius: 8 }} />
      )}
      {preview && preview.contentType === "application/pdf" && (
        <iframe src={preview.url} title={document.original_filename} style={{ width: "100%", height: "70vh", border: "none" }} />
      )}
      {preview && !preview.contentType.startsWith("image/") && preview.contentType !== "application/pdf" && (
        <div className="empty-state">
          No inline preview available for this file type ({preview.contentType}).
          Use Download to save it locally.
        </div>
      )}
    </Modal>
  );
}
