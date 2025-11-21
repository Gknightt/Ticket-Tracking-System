import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { BarChart3, Grid3X3, List } from "lucide-react";

// components
import AdminNav from "../../components/navigation/AdminNav";
import TimeFilter from "../../components/component/TimeFilter";
import ErrorBoundary from "../../components/ErrorBoundary";
import TicketTab from "./tabs/TicketTab";
import WorkflowTab from "./tabs/WorkflowTab";
import AgentTab from "./tabs/AgentTab";
import IntegrationTab from "./tabs/IntegrationTab";
import TaskItemTab from "./tabs/TaskItemTab";

// hooks
import useReportingAnalytics from "../../api/useReportingAnalytics";

// styles
import styles from "./report.module.css";

export default function Report() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get("tab") || "taskitem";
  const [activeTab, setActiveTab] = useState(tabFromUrl);
  const [timeFilter, setTimeFilter] = useState({ startDate: null, endDate: null });
  const [displayStyle, setDisplayStyle] = useState("charts"); // "charts", "grid", "list"
  
  // Unified reporting analytics hook
  const {
    loading,
    error,
    ticketsReport,
    workflowsReport,
    tasksReport,
    fetchAllAnalytics,
  } = useReportingAnalytics();

  // Fetch all analytics on component mount
  useEffect(() => {
    fetchAllAnalytics();
  }, [fetchAllAnalytics]);

  // Sync activeTab with URL query parameters
  useEffect(() => {
    const tabFromUrl = searchParams.get("tab") || "taskitem";
    setActiveTab(tabFromUrl);
  }, [searchParams]);

  // Refetch analytics when time filter changes
  useEffect(() => {
    if (timeFilter.startDate || timeFilter.endDate) {
      // Convert dates to ISO format (YYYY-MM-DD)
      const dateRange = {
        start_date: timeFilter.startDate ? timeFilter.startDate.toISOString().split('T')[0] : null,
        end_date: timeFilter.endDate ? timeFilter.endDate.toISOString().split('T')[0] : null,
      };
      fetchAllAnalytics(dateRange);
    }
  }, [timeFilter, fetchAllAnalytics]);

  const handleTabClick = (e, tab) => {
    e.preventDefault();
    setActiveTab(tab);
    setSearchParams({ tab });
  };

  const renderActiveTab = () => {
    const agentData = {
      ...ticketsReport,
      task_performance: tasksReport,
    };

    switch (activeTab) {
      case "taskitem":
        return <TaskItemTab displayStyle={displayStyle} timeFilter={timeFilter} analyticsData={tasksReport} loading={loading} error={error} />;
      case "agent":
        return <AgentTab displayStyle={displayStyle} timeFilter={timeFilter} analyticsData={agentData} loading={loading} error={error} />;
      case "ticket":
        return <TicketTab displayStyle={displayStyle} timeFilter={timeFilter} analyticsData={ticketsReport} loading={loading} error={error} />;
      case "workflow":
        return <WorkflowTab displayStyle={displayStyle} timeFilter={timeFilter} analyticsData={workflowsReport} loading={loading} error={error} />;
      case "integration":
        return <IntegrationTab displayStyle={displayStyle} analyticsData={ticketsReport} loading={loading} error={error} />;
      default:
        return <TaskItemTab displayStyle={displayStyle} timeFilter={timeFilter} analyticsData={tasksReport} loading={loading} error={error} />;
    }
  };

  // Show loading or error at top level
  if (error) {
    return (
      <>
        <AdminNav />
        <main className={styles.reportPage}>
          <section className={styles.rpHeader}>
            <h1>Reporting and Analytics</h1>
          </section>
          <section className={styles.rpBody}>
            <div style={{ color: "red", padding: "20px" }}>Error: {error}</div>
          </section>
        </main>
      </>
    );
  }

  return (
    <>
      <AdminNav />
      <main className={styles.reportPage}>
        <section className={styles.rpHeader}>
          <h1>Reporting and Analytics</h1>
        </section>

        <section className={styles.rpBody}>
          {/* Controls Row - Tabs and Display Styles */}
          <div className={styles.controlsRow}>
            {/* Tabs */}
            <div className={styles.rpTabs}>
              {["taskitem", "agent", "ticket", "workflow", "integration"].map((tab) => {
                const tabLabels = {
                  taskitem: "Tasks",
                  agent: "Agent",
                  ticket: "Ticket",
                  workflow: "Workflow",
                  integration: "Integration"
                };
                return (
                  <a
                    key={tab}
                    href="#"
                    onClick={(e) => handleTabClick(e, tab)}
                    className={`${styles.rpTabLink} ${
                      activeTab === tab ? styles.active : ""
                    }`}
                  >
                    {tabLabels[tab]}
                  </a>
                );
              })}
            </div>

            {/* Display Style Controls */}
            <div className={styles.displayControls}>
              <span className={styles.displayLabel}>Display:</span>
              <button
                onClick={() => setDisplayStyle("charts")}
                className={`${styles.displayBtn} ${displayStyle === "charts" ? styles.active : ""}`}
                title="Charts View"
              >
                <BarChart3 size={18} />
                Charts
              </button>
              <button
                onClick={() => setDisplayStyle("grid")}
                className={`${styles.displayBtn} ${displayStyle === "grid" ? styles.active : ""}`}
                title="Grid View"
              >
                <Grid3X3 size={18} />
                Grid
              </button>
              <button
                onClick={() => setDisplayStyle("list")}
                className={`${styles.displayBtn} ${displayStyle === "list" ? styles.active : ""}`}
                title="List View"
              >
                <List size={18} />
                List
              </button>
            </div>
          </div>

          {/* Time Filter */}
          <div className={styles.timeFilter}>
            <TimeFilter onFilterApply={setTimeFilter}/>
          </div>

          {/* Render Active Tab */}
          <ErrorBoundary>
            {renderActiveTab()}
          </ErrorBoundary>
        </section>
      </main>
    </>
  );
}