// hooks/useWorkflowProgress.js
import { useState, useEffect } from "react";
import api from "../axios"; // your custom axios instance

export function useWorkflowProgress(ticketID) {
  const [tracker, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!ticketID) return;

    setLoading(true);

    // Decide whether the provided identifier looks numeric (task_id) or a ticket number string
    const idStr = String(ticketID);
    const isNumeric = /^\d+$/.test(idStr);
    const param = isNumeric ? `task_id=${idStr}` : `ticket_id=${encodeURIComponent(idStr)}`;
    const url = `/tasks/workflow-visualization/?${param}`;

    // console.log("➡️ Requesting workflow visualization:", url);

    api
      .get(url)
      .then((res) => {
        // console.log("✅ API response (workflow visualization):", res.data);
        setData(res.data);
      })
      .catch((err) => {
        // Try to log useful info from axios error
        const status = err?.response?.status;
        const data = err?.response?.data;
        console.error("❌ API error (workflow visualization):", { message: err.message, status, data });
        setError(err);
      })
      .finally(() => setLoading(false));
  }, [ticketID]);

  return { tracker, loading, error };
}
