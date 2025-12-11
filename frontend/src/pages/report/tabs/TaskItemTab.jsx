// charts
import PieChart from "../../../components/charts/PieChart";
import BarChart from "../../../components/charts/BarChart";
import DoughnutChart from "../../../components/charts/DoughnutChart";
import ChartContainer from "../../../components/charts/ChartContainer";

// components
import DrilldownModal, { DRILLDOWN_COLUMNS } from "../components/DrilldownModal";

// hooks
import useDrilldownAnalytics from "../../../api/useDrilldownAnalytics";

// icons
import { AlertTriangle, GitBranch, Clock, Users, TrendingUp } from "lucide-react";

// react
import { useState } from "react";

// styles
import styles from "../report.module.css";

export default function TaskItemTab({
  displayStyle = "charts",
  timeFilter,
  analyticsData = {},
  loading,
  error,
}) {
  const tasksReport = analyticsData || {};

  // Drilldown state
  const [drilldownOpen, setDrilldownOpen] = useState(false);
  const [drilldownTitle, setDrilldownTitle] = useState('');
  const [drilldownColumns, setDrilldownColumns] = useState([]);
  const [drilldownParams, setDrilldownParams] = useState({});
  const [drilldownType, setDrilldownType] = useState('');
  
  const {
    loading: drilldownLoading,
    drilldownData,
    drilldownTaskItemsByStatus,
    drilldownTaskItemsByOrigin,
    drilldownUserTasks,
    drilldownTransfers,
    clearDrilldownData,
  } = useDrilldownAnalytics();

  if (loading) return <div style={{ padding: "20px" }}>Loading analytics...</div>;
  if (error) return <div style={{ color: "red", padding: "20px" }}>Error: {error}</div>;
  if (!tasksReport.status_distribution)
    return <div style={{ padding: "20px" }}>No task item data available</div>;

  // Extract data from aggregated response
  const summary = tasksReport.summary || {};
  const statusDist = tasksReport.status_distribution || [];
  const originDist = tasksReport.origin_distribution || [];
  const perf = tasksReport.performance || {};
  const userPerf = tasksReport.user_performance || [];
  const transfers = tasksReport.transfer_analytics || {};

  // Status distribution
  const statusLabels = statusDist.map((s) => s.status) || [];
  const statusCounts = statusDist.map((s) => s.count) || [];

  // Origin distribution
  const originLabels = originDist.map((o) => o.origin) || [];
  const originCounts = originDist.map((o) => o.count) || [];

  // Performance KPIs
  const timeToActionAvg = perf.time_to_action_hours?.average || 0;
  const slaCompliance = perf.sla_compliance?.summary?.current_compliance_rate_percent || 0;
  const activeItems = perf.active_items || 0;
  const overdueItems = perf.overdue_items || 0;

  // User Performance
  const userLabels = userPerf.map((u) => u.user_name || `User ${u.user_id}`) || [];
  const userResolved = userPerf.map((u) => u.resolved) || [];
  const userBreached = userPerf.map((u) => u.breached) || [];
  const userEscalated = userPerf.map((u) => u.escalated) || [];

  // Transfer & Escalation
  const transferrers = transfers.top_transferrers || [];
  const transferrerLabels = transferrers.map((t) => t.role_user__user_full_name || `User ${t.role_user__user_id}`);
  const transferrerCounts = transferrers.map((t) => t.transfer_count);

  const escalationsByStep = transfers.escalations_by_step || [];
  const escalationStepLabels = escalationsByStep.map((e) =>
    e.assigned_on_step__name?.split(" - ")[1] || e.assigned_on_step__name || "Unknown"
  );
  const escalationCounts = escalationsByStep.map((e) => e.escalation_count);

  // Drilldown handlers
  const handleStatusClick = async (status) => {
    setDrilldownTitle(`Task Items - ${status}`);
    setDrilldownColumns(DRILLDOWN_COLUMNS.taskItems);
    setDrilldownType('status');
    setDrilldownParams({ status });
    setDrilldownOpen(true);
    await drilldownTaskItemsByStatus({ 
      status, 
      start_date: timeFilter?.startDate?.toISOString()?.split('T')[0],
      end_date: timeFilter?.endDate?.toISOString()?.split('T')[0],
    });
  };

  const handleOriginClick = async (origin) => {
    setDrilldownTitle(`Task Items - ${origin}`);
    setDrilldownColumns(DRILLDOWN_COLUMNS.taskItems);
    setDrilldownType('origin');
    setDrilldownParams({ origin });
    setDrilldownOpen(true);
    await drilldownTaskItemsByOrigin({ 
      origin,
      start_date: timeFilter?.startDate?.toISOString()?.split('T')[0],
      end_date: timeFilter?.endDate?.toISOString()?.split('T')[0],
    });
  };

  const handleUserClick = async (userId, userName) => {
    setDrilldownTitle(`Tasks for ${userName}`);
    setDrilldownColumns(DRILLDOWN_COLUMNS.userTasks);
    setDrilldownType('user');
    setDrilldownParams({ user_id: userId });
    setDrilldownOpen(true);
    await drilldownUserTasks({ 
      user_id: userId,
      start_date: timeFilter?.startDate?.toISOString()?.split('T')[0],
      end_date: timeFilter?.endDate?.toISOString()?.split('T')[0],
    });
  };

  const handleTransferClick = async (origin = null) => {
    setDrilldownTitle(origin ? `${origin} Records` : 'Transfers & Escalations');
    setDrilldownColumns(DRILLDOWN_COLUMNS.transfers);
    setDrilldownType('transfer');
    setDrilldownParams({ origin });
    setDrilldownOpen(true);
    await drilldownTransfers({ 
      origin,
      start_date: timeFilter?.startDate?.toISOString()?.split('T')[0],
      end_date: timeFilter?.endDate?.toISOString()?.split('T')[0],
    });
  };

  const handleDrilldownPageChange = async (page) => {
    const params = { 
      ...drilldownParams, 
      page,
      start_date: timeFilter?.startDate?.toISOString()?.split('T')[0],
      end_date: timeFilter?.endDate?.toISOString()?.split('T')[0],
    };
    
    if (drilldownType === 'status') {
      await drilldownTaskItemsByStatus(params);
    } else if (drilldownType === 'origin') {
      await drilldownTaskItemsByOrigin(params);
    } else if (drilldownType === 'user') {
      await drilldownUserTasks(params);
    } else if (drilldownType === 'transfer') {
      await drilldownTransfers(params);
    }
  };

  const handleCloseDrilldown = () => {
    setDrilldownOpen(false);
    clearDrilldownData();
  };

  const kpiData = [
    {
      title: "Avg. Time to Action (hrs)",
      value: timeToActionAvg.toFixed(2),
      icon: <Clock size={28} color="#4a90e2" />,
    },
    {
      title: "SLA Compliance Rate (%)",
      value: slaCompliance.toFixed(1),
      icon: <TrendingUp size={28} color="#7ed321" />,
    },
    {
      title: "Active Items",
      value: activeItems,
      icon: <AlertTriangle size={28} color="#f5a623" />,
    },
    {
      title: "Overdue Items",
      value: overdueItems,
      icon: <AlertTriangle size={28} color="#e74c3c" />,
    },
    {
      title: "Total Transfers",
      value: transfers.total_transfers || 0,
      icon: <GitBranch size={28} color="#50e3c2" />,
    },
    {
      title: "Total Escalations",
      value: transfers.total_escalations || 0,
      icon: <TrendingUp size={28} color="#a850e3" />,
    },
  ];

  // Render different views based on displayStyle
  if (displayStyle === "list") {
    return (
      <div className={styles.rpTicketTabSection}>
        {/* Drilldown Modal */}
        <DrilldownModal
          isOpen={drilldownOpen}
          onClose={handleCloseDrilldown}
          title={drilldownTitle}
          data={drilldownData}
          columns={drilldownColumns}
          onPageChange={handleDrilldownPageChange}
          loading={drilldownLoading}
        />
        
        <div className={styles.chartSection}>
          <h2>Task Item KPI</h2>
          <div className={styles.listView}>
            {kpiData.map((card, idx) => (
              <div key={idx} className={styles.listItem}>
                <div className={styles.listItemContent}>
                  <span className={styles.listLabel}>{card.title}</span>
                  <span className={styles.listValue}>{card.value}</span>
                </div>
                <div className={styles.listIcon}>{card.icon}</div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.chartSection}>
          <h2>Status & Origin Distribution</h2>
          <div className={styles.listView}>
            <div className={styles.analyticsSection}>
              <h3>Task Status <span className={styles.clickHint}>(click to drill down)</span></h3>
              {statusLabels.map((label, idx) => (
                <div 
                  key={idx} 
                  className={`${styles.listItem} ${styles.clickable}`}
                  onClick={() => handleStatusClick(label)}
                >
                  <span className={styles.listLabel}>{label}</span>
                  <span className={styles.listValue}>{statusCounts[idx]}</span>
                </div>
              ))}
            </div>
            <div className={styles.analyticsSection}>
              <h3>Origin Distribution <span className={styles.clickHint}>(click to drill down)</span></h3>
              {originLabels.map((label, idx) => (
                <div 
                  key={idx} 
                  className={`${styles.listItem} ${styles.clickable}`}
                  onClick={() => handleOriginClick(label)}
                >
                  <span className={styles.listLabel}>{label}</span>
                  <span className={styles.listValue}>{originCounts[idx]}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className={styles.chartSection}>
          <h2>User Performance <span className={styles.clickHint}>(click user to drill down)</span></h2>
          <div className={styles.listView}>
            {userPerf.map((user, idx) => (
              <div 
                key={idx} 
                className={`${styles.analyticsSection} ${styles.clickable}`}
                onClick={() => handleUserClick(user.user_id, user.user_name)}
              >
                <h3>{user.user_name || `User ${user.user_id}`}</h3>
                <div className={styles.listItem}>
                  <span className={styles.listLabel}>Resolved</span>
                  <span className={styles.listValue}>{user.resolved}</span>
                </div>
                <div className={styles.listItem}>
                  <span className={styles.listLabel}>Escalated</span>
                  <span className={styles.listValue}>{user.escalated}</span>
                </div>
                <div className={styles.listItem}>
                  <span className={styles.listLabel}>Breached</span>
                  <span className={styles.listValue}>{user.breached}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (displayStyle === "grid") {
    return (
      <div className={styles.rpTicketTabSection}>
        {/* Drilldown Modal */}
        <DrilldownModal
          isOpen={drilldownOpen}
          onClose={handleCloseDrilldown}
          title={drilldownTitle}
          data={drilldownData}
          columns={drilldownColumns}
          onPageChange={handleDrilldownPageChange}
          loading={drilldownLoading}
        />
        
        <div className={styles.chartSection}>
          <h2>Task Item KPI</h2>
          <div className={styles.gridTable}>
            <div className={styles.gridHeader}>
              <div>Metric</div>
              <div>Value</div>
            </div>
            {kpiData.map((card, idx) => (
              <div key={idx} className={styles.gridRow}>
                <div>{card.title}</div>
                <div>{card.value}</div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.chartSection}>
          <h2>Task Status Distribution <span className={styles.clickHint}>(click to drill down)</span></h2>
          <div className={styles.gridTable}>
            <div className={styles.gridHeader}>
              <div>Status</div>
              <div>Count</div>
            </div>
            {statusLabels.map((label, idx) => (
              <div 
                key={idx} 
                className={`${styles.gridRow} ${styles.clickable}`}
                onClick={() => handleStatusClick(label)}
              >
                <div>{label}</div>
                <div>{statusCounts[idx]}</div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.chartSection}>
          <h2>Assignment Origin Distribution <span className={styles.clickHint}>(click to drill down)</span></h2>
          <div className={styles.gridTable}>
            <div className={styles.gridHeader}>
              <div>Origin</div>
              <div>Count</div>
            </div>
            {originLabels.map((label, idx) => (
              <div 
                key={idx} 
                className={`${styles.gridRow} ${styles.clickable}`}
                onClick={() => handleOriginClick(label)}
              >
                <div>{label}</div>
                <div>{originCounts[idx]}</div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.chartSection}>
          <h2>User Performance Details <span className={styles.clickHint}>(click user to drill down)</span></h2>
          <div className={styles.gridTable}>
            <div className={styles.gridHeader}>
              <div>User</div>
              <div>Resolved</div>
              <div>Escalated</div>
              <div>Breached</div>
            </div>
            {userPerf.map((user, idx) => (
              <div 
                key={idx} 
                className={`${styles.gridRow} ${styles.clickable}`}
                onClick={() => handleUserClick(user.user_id, user.user_name)}
              >
                <div>{user.user_name || `User ${user.user_id}`}</div>
                <div>{user.resolved}</div>
                <div>{user.escalated}</div>
                <div>{user.breached}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.rpTicketTabSection}>
      {/* Drilldown Modal */}
      <DrilldownModal
        isOpen={drilldownOpen}
        onClose={handleCloseDrilldown}
        title={drilldownTitle}
        data={drilldownData}
        columns={drilldownColumns}
        onPageChange={handleDrilldownPageChange}
        loading={drilldownLoading}
      />
      
      {/* KPI */}
      <div className={styles.chartSection}>
        <h2>Task Item KPI</h2>
        <div className={styles.kpiGrid}>
          {kpiData.map((card, index) => (
            <div key={index} className={styles.kpiCard}>
              <div>
                <p>{card.title}</p>
                <h2>{card.value}</h2>
              </div>
              <div>
                <span className={styles.kpiIcon}>{card.icon}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Task Item Status & Origin */}
      <div className={styles.chartsGrid}>
        <div className={styles.chartSection}>
          <h2>Task Item Status Distribution <span className={styles.clickHint}>(click to drill down)</span></h2>
          <div className={styles.chartRow}>
            <ChartContainer title="Task Item Status Breakdown">
              <PieChart
                labels={statusLabels}
                dataPoints={statusCounts}
                chartTitle="Task Item Status"
                chartLabel="Count"
                onClick={({ label }) => handleStatusClick(label)}
              />
            </ChartContainer>

            <ChartContainer title="Assignment Origin Distribution">
              <DoughnutChart
                labels={originLabels}
                values={originCounts}
                chartTitle="Assignment Origin"
                chartLabel="Count"
                onClick={({ label }) => handleOriginClick(label)}
              />
            </ChartContainer>
          </div>
        </div>
      </div>

      {/* Transfer & Escalation Analytics */}
      <div className={styles.chartsGrid}>
        <div className={styles.chartSection}>
          <h2>Transfer & Escalation Analytics <span className={styles.clickHint}>(click to drill down)</span></h2>
          <div className={styles.chartRow}>
            <ChartContainer title="Top Task Transferrers">
              <BarChart
                labels={transferrerLabels}
                dataPoints={transferrerCounts}
                chartTitle="Task Transfers"
                chartLabel="Count"
                onClick={() => handleTransferClick('Transferred')}
              />
            </ChartContainer>

            <ChartContainer title="Escalations by Step">
              <BarChart
                labels={escalationStepLabels}
                dataPoints={escalationCounts}
                chartTitle="Escalations"
                chartLabel="Count"
                onClick={() => handleTransferClick('Escalation')}
              />
            </ChartContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
