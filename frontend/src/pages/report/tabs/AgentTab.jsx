import { useMemo } from "react";

// charts
import PieChart from "../../../components/charts/PieChart";
import BarChart from "../../../components/charts/BarChart";
import DoughnutChart from "../../../components/charts/DoughnutChart";
import ChartContainer from "../../../components/charts/ChartContainer";

// styles
import styles from "../report.module.css";

export default function AgentTab({ timeFilter, analyticsData = {}, loading, error }) {
  const { teamPerformance, slaCompliance, assignmentAnalytics } = analyticsData;

  if (loading) return <div style={{ padding: "20px" }}>Loading analytics...</div>;
  if (error) return <div style={{ color: "red", padding: "20px" }}>Error: {error}</div>;
  if (!teamPerformance && !slaCompliance && !assignmentAnalytics)
    return <div style={{ padding: "20px" }}>No agent data available</div>;

  // Extract data from analytics - use user_name from backend
  const teamLabels = teamPerformance?.map(t => t.user_name || `User ${t.user_id}`) || [];
  const teamTicketsHandled = teamPerformance?.map(t => t.total_tasks) || [];
  const teamAvgTime = teamPerformance?.map(t => Math.round(t.avg_resolution_hours || 0)) || [];

  // SLA compliance is by priority, not by agent - use priority labels
  const slaLabels = slaCompliance?.map(s => s.priority) || [];
  const slaCompliances = slaCompliance?.map(s => Math.round(s.compliance_rate || 0)) || [];

  // Assignment analytics by role
  const assignmentLabels = assignmentAnalytics?.map(a => a.role_name) || [];
  const assignmentCounts = assignmentAnalytics?.map(a => a.total_assignments) || [];

  return (
    <div className={styles.chartsGrid}>
      {/* Agent Performance */}
      <div className={styles.chartSection}>
        <h2>Agent Performance</h2>
        <div className={styles.chartRow}>
          <ChartContainer title="Tickets Handled per Agent">
            <DoughnutChart
              labels={teamLabels}
              values={teamTicketsHandled}
              chartTitle="Tickets Handled per Agent"
              chartLabel="Tickets"
            />
          </ChartContainer>

          <ChartContainer title="Average Response Time by Agent">
            <BarChart
              labels={teamLabels}
              dataPoints={teamAvgTime}
              chartTitle="Avg Response Time (mins)"
              chartLabel="Minutes"
            />
          </ChartContainer>
        </div>
      </div>

      {/* SLA & Assignment Insights */}
      <div className={styles.chartSection}>
        <h2>SLA & Assignment Insights</h2>
        <div className={styles.chartRow}>
          <ChartContainer title="SLA Compliance by Priority">
            <BarChart
              labels={slaLabels}
              dataPoints={slaCompliances}
              chartTitle="SLA Compliance (%)"
              chartLabel="Percentage"
            />
          </ChartContainer>

          <ChartContainer title="Assignment Distribution by Role">
            <PieChart
              labels={assignmentLabels}
              dataPoints={assignmentCounts}
              chartTitle="Assignment Distribution"
              chartLabel="Assignments"
            />
          </ChartContainer>
        </div>
      </div>
    </div>
  );
}
