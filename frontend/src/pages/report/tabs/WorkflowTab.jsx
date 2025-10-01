// charts
import BarChart from "../../../components/charts/BarChart";
import LineChart from "../../../components/charts/LineChart";
import ChartContainer from "../../../components/charts/ChartContainer";

// styles
import styles from "../report.module.css";

// hooks
import useFetchWorkflows from "../../../api/useFetchWorkflows";
import { Doughnut, Pie } from "react-chartjs-2";
import DoughnutChart from "../../../components/charts/DoughnutChart";
import PieChart from "../../../components/charts/PieChart";

// Helper function to count occurrences by field
const countByField = (data, field) => {
  return data.reduce((acc, item) => {
    const key = item[field] || "Unknown";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
};

export default function WorkflowTab() {
  const { workflows, refetch, loading, error } = useFetchWorkflows();

  console.log("Fetched workflows:", workflows);

  if (loading) return <div>Loading data, please wait...</div>;
  if (error)
    return <div>Error: {error.message || "An unexpected error occurred"}</div>;
  if (!workflows || workflows.length === 0)
    return <div>No data available.</div>;

  // Prepare data
  const categoryCounts = countByField(workflows, "category");
  const statusCounts = countByField(workflows, "status");
  const departmentCounts = countByField(workflows, "department");

  return (
    <div className={styles.chartsGrid}>
      <div className={styles.chartSection}>
        <h2>Workflow Analytics</h2>
        <div className={styles.chartRow}>
          {/* Chart 2: Workflows by Status */}
          <ChartContainer title="Workflows by Status">
            <DoughnutChart
              labels={Object.keys(statusCounts)}
              values={Object.values(statusCounts)}
              chartTitle="Workflows per Status"
              chartLabel="Number of Workflows"
            />
            {/* <DoughnutChart
              labels={["Acted", "Not Acted"]}
              values={[actedCount, notActedCount]}
              chartLabel="Tickets"
              chartTitle="Acted vs Not Acted Tickets"
            /> */}
          </ChartContainer>

          {/* Chart 1: Workflows by Category */}
          <ChartContainer title="Workflows by Category">
            <PieChart
              labels={Object.keys(categoryCounts)}
              dataPoints={Object.values(categoryCounts)}
              chartTitle="Workflows per Category"
              chartLabel="Number of Workflows"
            />
          </ChartContainer>

          {/* Chart 3: Workflows by Department */}
          <ChartContainer title="Workflows by Department">
            <PieChart
              labels={Object.keys(departmentCounts)}
              dataPoints={Object.values(departmentCounts)}
              chartTitle="Workflows per Department"
              chartLabel="Number of Workflows"
            />
          </ChartContainer>
        </div>
      </div>
    </div>
  );
}
