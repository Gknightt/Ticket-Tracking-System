import PieChart from "../../../components/charts/PieChart";
import BarChart from "../../../components/charts/BarChart";
import ChartContainer from "../../../components/charts/ChartContainer";
import IntegrationStatusCard from "../components/IntegrationStatusCard";
import styles from "../report.module.css";

export default function IntegrationTab({ analyticsData = {}, loading, error }) {
  const { auditActivity } = analyticsData;

  if (loading) return <div style={{ padding: "20px" }}>Loading analytics...</div>;
  if (error) return <div style={{ color: "red", padding: "20px" }}>Error: {error}</div>;
  if (!auditActivity)
    return <div style={{ padding: "20px" }}>No audit data available</div>;

  // Extract audit activity data
  const actionLabels = auditActivity?.map(a => a.action_type) || [];
  const actionCounts = auditActivity?.map(a => a.count) || [];

  return (
    <div className={styles.chartsGrid}>
      <div className={styles.chartSection}>
        <h2>Audit Activity</h2>
        <div className={styles.chartRow}>
          <IntegrationStatusCard />
        </div>
      </div>
      <div className={styles.chartSection}>
        <h2>Audit Metrics</h2>
        <div className={styles.chartRow}>
          <ChartContainer title="Actions by Type">
            <PieChart
              labels={actionLabels}
              dataPoints={actionCounts}
              chartTitle="Audit Actions by Type"
              chartLabel="Count"
            />
          </ChartContainer>
          <ChartContainer title="Action Distribution">
            <BarChart
              labels={actionLabels}
              dataPoints={actionCounts}
              chartTitle="Action Distribution"
              chartLabel="Count"
            />
          </ChartContainer>
        </div>
      </div>
    </div>
  );
}
