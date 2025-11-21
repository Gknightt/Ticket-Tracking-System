// charts
import PieChart from "../../../components/charts/PieChart";
import BarChart from "../../../components/charts/BarChart";
import ChartContainer from "../../../components/charts/ChartContainer";

// icons
import {
  Ticket,
  FolderOpen,
  CheckCircle,
  Clock,
  HardDrive,
} from "lucide-react";

// styles
import styles from "../report.module.css";

export default function TicketTab({ timeFilter, analyticsData = {}, loading, error }) {
  const { dashboard, statusSummary, priorityDistribution, ticketAge } = analyticsData;

  if (loading) return <div style={{ padding: "20px" }}>Loading analytics...</div>;
  if (error) return <div style={{ color: "red", padding: "20px" }}>Error: {error}</div>;
  if (!dashboard) return <div style={{ padding: "20px" }}>No data available</div>;

  // Storage used (fallback if not available)
  // Extract analytics data
  const totalTickets = dashboard?.total_tickets || 0;
  const openTickets = dashboard?.open_tickets || 0;
  const closedTickets = dashboard?.closed_tickets || 0;
  const avgResolutionTime = Math.round(dashboard?.avg_resolution_time || 0);

  const kpiCardData = [
    {
      title: "Total Tickets",
      value: totalTickets,
      icon: <Ticket size={28} color="#4a90e2" />,
    },
    {
      title: "Open Tickets",
      value: openTickets,
      icon: <FolderOpen size={28} color="#f5a623" />,
    },
    {
      title: "Closed Tickets",
      value: closedTickets,
      icon: <CheckCircle size={28} color="#7ed321" />,
    },
    {
      title: "Avg. Resolution Time (hrs)",
      value: avgResolutionTime,
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

  return (
    <div className={styles.rpTicketTabSection}>
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
          <h2>Ticket Analytics</h2>
          <div className={styles.chartRow}>
            <ChartContainer title="Tickets by Status">
              <PieChart
                labels={statusLabels}
                dataPoints={statusDataPoints}
                chartTitle="Tickets by Status"
                chartLabel="Status"
              />
            </ChartContainer>
            <ChartContainer title="Tickets by Priority">
              <PieChart
                labels={priorityLabels}
                dataPoints={priorityDataPoints}
                chartTitle="Tickets by Priority"
                chartLabel="Priority"
              />
            </ChartContainer>
            <ChartContainer title="Ticket Age Distribution">
              <BarChart
                labels={ageLabels}
                dataPoints={ageDataPoints}
                chartTitle="Ticket Age Distribution"
                chartLabel="Count"
              />
            </ChartContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
