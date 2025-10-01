import BarChart from "../../../components/charts/BarChart";
import LineChart from "../../../components/charts/LineChart";
import ChartContainer from "../../../components/charts/ChartContainer";
import styles from "../report.module.css";
import { useWorkflowReportData } from "../reportHooks";

export default function WorkflowTab() {
  const { data: reportData, loading, error } = useWorkflowReportData();

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!reportData) return <div>No data available.</div>;

  return (
    <div className={styles.chartsGrid}>
      {/* Workflow Analytics */}
      <div className={styles.chartSection}>
        <h2>Workflow Analytics</h2>
        <div className={styles.chartRow}>
          <ChartContainer title="Workflow Usage">
            <BarChart
              labels={reportData.workflows.map((w) => w.name)}
              dataPoints={reportData.workflows.map((w) => w.usage)}
              chartTitle="Workflow Usage"
              chartLabel="Usage"
            />
          </ChartContainer>
          <ChartContainer title="Workflow Completion Rates">
            <BarChart
              labels={reportData.workflows.map((w) => w.name)}
              dataPoints={reportData.workflows.map((w) => w.completionRate * 100)}
              chartTitle="Workflow Completion Rates (%)"
              chartLabel="Completion Rate"
            />
          </ChartContainer>
          <ChartContainer title="Average Time per Workflow Step">
            <LineChart
              labels={reportData.workflows.map((w) => w.name)}
              dataPoints={reportData.workflows.map((w) => parseFloat(w.avgStepTime))}
              chartTitle="Average Step Time (h)"
              chartLabel="Avg Step Time"
            />
          </ChartContainer>
        </div>
      </div>
    </div>
  );
}