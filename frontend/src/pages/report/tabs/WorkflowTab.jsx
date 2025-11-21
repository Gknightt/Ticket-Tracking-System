// react
import { useMemo } from "react";

// charts
import BarChart from "../../../components/charts/BarChart";
import ChartContainer from "../../../components/charts/ChartContainer";
import PieChart from "../../../components/charts/PieChart";

// styles
import styles from "../report.module.css";

// Helper function to count occurrences by field
const countByField = (data, field) => {
  return data.reduce((acc, item) => {
    const key = item[field] || "Unknown";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
};

export default function WorkflowTab({ displayStyle = "charts", timeFilter, analyticsData = {}, loading, error }) {
  const workflowsReport = analyticsData || {};

  if (loading) return <div style={{ padding: "20px" }}>Loading analytics...</div>;
  if (error) return <div style={{ color: "red", padding: "20px" }}>Error: {error}</div>;
  if (!workflowsReport.workflow_metrics && !workflowsReport.department_analytics && !workflowsReport.step_performance)
    return <div style={{ padding: "20px" }}>No workflow data available</div>;

  // Extract data from aggregated response
  const workflowMetrics = workflowsReport.workflow_metrics || [];
  const departmentAnalytics = workflowsReport.department_analytics || [];
  const stepPerformance = workflowsReport.step_performance || [];

  // Extract data from analytics
  const workflowLabels = workflowMetrics?.map(w => w.workflow_name) || [];
  const workflowDataPoints = workflowMetrics?.map(w => w.total_tasks) || [];
  const workflowCompletionRates = workflowMetrics?.map(w => Math.round(w.completion_rate || 0)) || [];

  const deptLabels = departmentAnalytics?.map(d => d.department) || [];
  const deptDataPoints = departmentAnalytics?.map(d => d.total_tickets) || [];
  const deptCompletionRates = departmentAnalytics?.map(d => Math.round(d.completion_rate || 0)) || [];

  const stepLabels = stepPerformance?.map(s => s.step_name?.split(' - ')[1] || s.step_name) || [];
  const stepDataPoints = stepPerformance?.map(s => s.total_tasks) || [];

  // Render different views based on displayStyle
  if (displayStyle === "list") {
    return (
      <div className={styles.rpTicketTabSection}>
        <div className={styles.chartSection}>
          <h2>Workflow Analytics</h2>
          <div className={styles.listView}>
            <div className={styles.analyticsSection}>
              <h3>Workflows by Execution Count</h3>
              {workflowLabels.map((label, idx) => (
                <div key={idx} className={styles.listItem}>
                  <span className={styles.listLabel}>{label}</span>
                  <span className={styles.listValue}>{workflowDataPoints[idx]}</span>
                </div>
              ))}
            </div>
            <div className={styles.analyticsSection}>
              <h3>Workflows by Department</h3>
              {deptLabels.map((label, idx) => (
                <div key={idx} className={styles.listItem}>
                  <span className={styles.listLabel}>{label}</span>
                  <span className={styles.listValue}>{deptDataPoints[idx]}</span>
                </div>
              ))}
            </div>
            <div className={styles.analyticsSection}>
              <h3>Workflow Completion Rates</h3>
              {workflowLabels.map((label, idx) => (
                <div key={idx} className={styles.listItem}>
                  <span className={styles.listLabel}>{label}</span>
                  <span className={styles.listValue}>{workflowCompletionRates[idx]}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (displayStyle === "grid") {
    return (
      <div className={styles.rpTicketTabSection}>
        <div className={styles.chartSection}>
          <h2>Workflows by Execution Count</h2>
          <div className={styles.gridTable}>
            <div className={styles.gridHeader}>
              <div>Workflow Name</div>
              <div>Total Tasks</div>
            </div>
            {workflowLabels.map((label, idx) => (
              <div key={idx} className={styles.gridRow}>
                <div>{label}</div>
                <div>{workflowDataPoints[idx]}</div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.chartSection}>
          <h2>Workflows by Department</h2>
          <div className={styles.gridTable}>
            <div className={styles.gridHeader}>
              <div>Department</div>
              <div>Total Tickets</div>
              <div>Completion Rate %</div>
            </div>
            {deptLabels.map((label, idx) => (
              <div key={idx} className={styles.gridRow}>
                <div>{label}</div>
                <div>{deptDataPoints[idx]}</div>
                <div>{deptCompletionRates[idx]}%</div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.chartSection}>
          <h2>Workflow Completion Rates</h2>
          <div className={styles.gridTable}>
            <div className={styles.gridHeader}>
              <div>Workflow</div>
              <div>Completion Rate %</div>
            </div>
            {workflowLabels.map((label, idx) => (
              <div key={idx} className={styles.gridRow}>
                <div>{label}</div>
                <div>{workflowCompletionRates[idx]}%</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.chartsGrid}>
      <div className={styles.chartSection}>
        <h2>Workflow Analytics</h2>
        <div className={styles.chartRow}>
          {/* Chart 1: Workflows */}
          <ChartContainer title="Workflows by Execution Count">
            <BarChart
              labels={workflowLabels}
              dataPoints={workflowDataPoints}
              chartTitle="Workflows by Execution Count"
              chartLabel="Count"
            />
          </ChartContainer>

          {/* Chart 2: Department Analytics */}
          <ChartContainer title="Workflows by Department">
            <PieChart
              labels={deptLabels}
              dataPoints={deptDataPoints}
              chartTitle="Workflows per Department"
              chartLabel="Number of Workflows"
            />
          </ChartContainer>

          {/* Chart 3: Workflow Completion Rates */}
          <ChartContainer title="Workflow Completion Rates">
            <BarChart
              labels={workflowLabels}
              dataPoints={workflowCompletionRates}
              chartTitle="Workflow Completion Rate (%)"
              chartLabel="Percentage"
            />
          </ChartContainer>
        </div>
      </div>
    </div>
  );
}
