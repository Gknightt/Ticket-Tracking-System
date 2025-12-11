// charts
import PieChart from "../../../components/charts/PieChart";
import BarChart from "../../../components/charts/BarChart";
import ChartContainer from "../../../components/charts/ChartContainer";

// components
import DrilldownModal, { DRILLDOWN_COLUMNS } from "../components/DrilldownModal";

// hooks
import useDrilldownAnalytics from "../../../api/useDrilldownAnalytics";

// icons
import {
  Ticket,
  FolderOpen,
  CheckCircle,
  Clock,
  HardDrive,
} from "lucide-react";

// react
import { useState } from "react";

// styles
import styles from "../report.module.css";

export default function TicketTab({ displayStyle = "charts", timeFilter, analyticsData = {}, loading, error }) {
  const ticketsReport = analyticsData || {};
  
  // Drilldown state
  const [drilldownOpen, setDrilldownOpen] = useState(false);
  const [drilldownTitle, setDrilldownTitle] = useState('');
  const [drilldownColumns, setDrilldownColumns] = useState([]);
  const [drilldownParams, setDrilldownParams] = useState({});
  const [drilldownType, setDrilldownType] = useState('');
  
  const {
    loading: drilldownLoading,
    drilldownData,
    drilldownTicketsByStatus,
    drilldownTicketsByPriority,
    drilldownTicketsByAge,
    drilldownSLACompliance,
    clearDrilldownData,
  } = useDrilldownAnalytics();

  if (loading) return <div style={{ padding: "20px" }}>Loading analytics...</div>;
  if (error) return <div style={{ color: "red", padding: "20px" }}>Error: {error}</div>;
  if (!ticketsReport.dashboard) return <div style={{ padding: "20px" }}>No data available</div>;

  // Extract analytics data from aggregated response
  const dashboard = ticketsReport.dashboard || {};
  const statusSummary = ticketsReport.status_summary || [];
  const priorityDistribution = ticketsReport.priority_distribution || [];
  const ticketAge = ticketsReport.ticket_age || [];

  // Storage used (fallback if not available)
  const totalTickets = dashboard?.total_tickets || 0;
  const completedTickets = dashboard?.completed_tickets || 0;
  const pendingTickets = dashboard?.pending_tickets || 0;
  const inProgressTickets = dashboard?.in_progress_tickets || 0;
  const avgResolutionTime = dashboard?.avg_resolution_time_hours || 0;
  const slaCompliance = dashboard?.sla_compliance_rate || 0;
  const escalationRate = dashboard?.escalation_rate || 0;

  // Drilldown handlers
  const handleStatusClick = async (status) => {
    setDrilldownTitle(`Tickets - ${status}`);
    setDrilldownColumns(DRILLDOWN_COLUMNS.tickets);
    setDrilldownType('status');
    setDrilldownParams({ status });
    setDrilldownOpen(true);
    await drilldownTicketsByStatus({ 
      status, 
      start_date: timeFilter?.startDate?.toISOString()?.split('T')[0],
      end_date: timeFilter?.endDate?.toISOString()?.split('T')[0],
    });
  };

  const handlePriorityClick = async (priority) => {
    setDrilldownTitle(`Tickets - ${priority} Priority`);
    setDrilldownColumns(DRILLDOWN_COLUMNS.tickets);
    setDrilldownType('priority');
    setDrilldownParams({ priority });
    setDrilldownOpen(true);
    await drilldownTicketsByPriority({ 
      priority,
      start_date: timeFilter?.startDate?.toISOString()?.split('T')[0],
      end_date: timeFilter?.endDate?.toISOString()?.split('T')[0],
    });
  };

  const handleAgeClick = async (ageBucket) => {
    setDrilldownTitle(`Tickets - ${ageBucket}`);
    setDrilldownColumns(DRILLDOWN_COLUMNS.ticketsSimple);
    setDrilldownType('age');
    setDrilldownParams({ age_bucket: ageBucket });
    setDrilldownOpen(true);
    await drilldownTicketsByAge({ age_bucket: ageBucket });
  };

  const handleDrilldownPageChange = async (page) => {
    const params = { 
      ...drilldownParams, 
      page,
      start_date: timeFilter?.startDate?.toISOString()?.split('T')[0],
      end_date: timeFilter?.endDate?.toISOString()?.split('T')[0],
    };
    
    if (drilldownType === 'status') {
      await drilldownTicketsByStatus(params);
    } else if (drilldownType === 'priority') {
      await drilldownTicketsByPriority(params);
    } else if (drilldownType === 'age') {
      await drilldownTicketsByAge(params);
    }
  };

  const handleCloseDrilldown = () => {
    setDrilldownOpen(false);
    clearDrilldownData();
  };

  const kpiCardData = [
    {
      title: "Total Tickets",
      value: totalTickets,
      icon: <Ticket size={28} color="#4a90e2" />,
    },
    {
      title: "Completed Tickets",
      value: completedTickets,
      icon: <CheckCircle size={28} color="#7ed321" />,
    },
    {
      title: "Pending Tickets",
      value: pendingTickets,
      icon: <FolderOpen size={28} color="#f5a623" />,
    },
    {
      title: "In Progress Tickets",
      value: inProgressTickets,
      icon: <Clock size={28} color="#50e3c2" />,
    },
    {
      title: "Pending Tickets",
      value: dashboard?.pending_tickets || 0,
      icon: <HardDrive size={28} color="#a850e3ff" />,
    },
  ];

  // Priority distribution data
  const priorityLabels = priorityDistribution?.map(p => p.priority) || [];
  const priorityDataPoints = priorityDistribution?.map(p => p.count) || [];

  // Status summary data
  const statusLabels = statusSummary?.map(s => s.status) || [];
  const statusDataPoints = statusSummary?.map(s => s.count) || [];

  // Ticket age data - backend returns age_bucket not age_range
  const ageLabels = ticketAge?.map(t => t.age_bucket) || [];
  const ageDataPoints = ticketAge?.map(t => t.count) || [];

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
        
        {/* KPI as List */}
        <div className={styles.chartSection}>
          <h2>Ticket KPI</h2>
          <div className={styles.listView}>
            {kpiCardData.map((card, index) => (
              <div key={index} className={styles.listItem}>
                <div className={styles.listItemContent}>
                  <span className={styles.listLabel}>{card.title}</span>
                  <span className={styles.listValue}>{card.value}</span>
                </div>
                <div className={styles.listIcon}>{card.icon}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Analytics as List */}
        <div className={styles.chartSection}>
          <h2>Ticket Analytics</h2>
          <div className={styles.listView}>
            <div className={styles.analyticsSection}>
              <h3>By Status <span className={styles.clickHint}>(click to drill down)</span></h3>
              {statusLabels.map((label, idx) => (
                <div 
                  key={idx} 
                  className={`${styles.listItem} ${styles.clickable}`}
                  onClick={() => handleStatusClick(label)}
                >
                  <span className={styles.listLabel}>{label}</span>
                  <span className={styles.listValue}>{statusDataPoints[idx]}</span>
                </div>
              ))}
            </div>
            <div className={styles.analyticsSection}>
              <h3>By Priority <span className={styles.clickHint}>(click to drill down)</span></h3>
              {priorityLabels.map((label, idx) => (
                <div 
                  key={idx} 
                  className={`${styles.listItem} ${styles.clickable}`}
                  onClick={() => handlePriorityClick(label)}
                >
                  <span className={styles.listLabel}>{label}</span>
                  <span className={styles.listValue}>{priorityDataPoints[idx]}</span>
                </div>
              ))}
            </div>
            <div className={styles.analyticsSection}>
              <h3>By Age <span className={styles.clickHint}>(click to drill down)</span></h3>
              {ageLabels.map((label, idx) => (
                <div 
                  key={idx} 
                  className={`${styles.listItem} ${styles.clickable}`}
                  onClick={() => handleAgeClick(label)}
                >
                  <span className={styles.listLabel}>{label}</span>
                  <span className={styles.listValue}>{ageDataPoints[idx]}</span>
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
        
        {/* KPI as Grid Table */}
        <div className={styles.chartSection}>
          <h2>Ticket KPI</h2>
          <div className={styles.gridTable}>
            <div className={styles.gridHeader}>
              <div>Metric</div>
              <div>Value</div>
            </div>
            {kpiCardData.map((card, index) => (
              <div key={index} className={styles.gridRow}>
                <div>{card.title}</div>
                <div>{card.value}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Analytics as Grid Tables */}
        <div className={styles.chartSection}>
          <h2>Ticket Analytics - Status <span className={styles.clickHint}>(click row to drill down)</span></h2>
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
                <div>{statusDataPoints[idx]}</div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.chartSection}>
          <h2>Ticket Analytics - Priority <span className={styles.clickHint}>(click row to drill down)</span></h2>
          <div className={styles.gridTable}>
            <div className={styles.gridHeader}>
              <div>Priority</div>
              <div>Count</div>
            </div>
            {priorityLabels.map((label, idx) => (
              <div 
                key={idx} 
                className={`${styles.gridRow} ${styles.clickable}`}
                onClick={() => handlePriorityClick(label)}
              >
                <div>{label}</div>
                <div>{priorityDataPoints[idx]}</div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.chartSection}>
          <h2>Ticket Analytics - Age <span className={styles.clickHint}>(click row to drill down)</span></h2>
          <div className={styles.gridTable}>
            <div className={styles.gridHeader}>
              <div>Age Bucket</div>
              <div>Count</div>
            </div>
            {ageLabels.map((label, idx) => (
              <div 
                key={idx} 
                className={`${styles.gridRow} ${styles.clickable}`}
                onClick={() => handleAgeClick(label)}
              >
                <div>{label}</div>
                <div>{ageDataPoints[idx]}</div>
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
        <h2>Ticket KPI</h2>
        <div className={styles.kpiGrid}>
          {kpiCardData.map((card, index) => (
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

      {/* chartsGrid - Ticket*/}
      <div className={styles.chartsGrid}>
        {/* Ticket Analytics Section */}
        <div className={styles.chartSection}>
          <h2>Ticket Analytics <span className={styles.clickHint}>(click chart segments to drill down)</span></h2>
          <div className={styles.chartRow}>
            <ChartContainer title="Tickets by Status">
              <PieChart
                labels={statusLabels}
                dataPoints={statusDataPoints}
                chartTitle="Tickets by Status"
                chartLabel="Status"
                onClick={({ label }) => handleStatusClick(label)}
              />
            </ChartContainer>
            <ChartContainer title="Tickets by Priority">
              <PieChart
                labels={priorityLabels}
                dataPoints={priorityDataPoints}
                chartTitle="Tickets by Priority"
                chartLabel="Priority"
                onClick={({ label }) => handlePriorityClick(label)}
              />
            </ChartContainer>
            <ChartContainer title="Ticket Age Distribution">
              <BarChart
                labels={ageLabels}
                dataPoints={ageDataPoints}
                chartTitle="Ticket Age Distribution"
                chartLabel="Count"
                onClick={({ label }) => handleAgeClick(label)}
              />
            </ChartContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
