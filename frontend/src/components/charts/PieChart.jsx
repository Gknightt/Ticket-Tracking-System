// PieChart.jsx

import { Pie } from "react-chartjs-2";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

// style
import styles from "./chart.module.css";

ChartJS.register(ArcElement, Tooltip, Legend);

export default function PieChart({
  labels,
  dataPoints,
  chartTitle = "Active Users Document Count",
  chartLabel = "Active User Documents",
}) {
  const data = {
    labels,
    datasets: [
      {
        label: chartLabel,
        data: dataPoints,
        backgroundColor: [
          "#00afb9", // Soft blue-gray for a gentle contrast
          "#f07167", // Light, muted green for a natural vibe
          "#0081a7", // Pale cream for balance and soft lightness
          "#f2cc8f", // Soft coral for a warm, inviting touch
          "#fed9b7", // Light lavender for a calm, soothing effect
          "#c4f0f2", // Soft mint for freshness and clarity
        ],
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: { position: "bottom" },
      title: {
        display: true,
        text: chartTitle,
      },
    },
  };

  return (
    <div className={styles.chartCardCont}>
      <Pie data={data} options={options} />
    </div>
  );
}
