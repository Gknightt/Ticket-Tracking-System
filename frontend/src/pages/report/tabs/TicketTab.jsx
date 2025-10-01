import { useEffect, useState } from "react";

// charts
import PieChart from "../../../components/charts/PieChart";
import BarChart from "../../../components/charts/BarChart";
import LineChart from "../../../components/charts/LineChart";
import ChartContainer from "../../../components/charts/ChartContainer";

// table
import TicketTable from "../../../tables/admin/TicketTable";

// date helper
import { format } from "date-fns";

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
import general from "../../../style/general.module.css";

// hooks
import useTicketsFetcher from "../../../api/useTicketsFetcher";
import DynamicTable from "../../../tables/components/DynamicTable";

export default function TicketTab() {
  const [error, setError] = useState(null);
  const {
    tickets,
    fetchTickets,
    loading: ticketsLoading,
    error: ticketsError,
  } = useTicketsFetcher();

  // call fetchTickets once on mount
  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  if (ticketsLoading) return <div>Loading...</div>;
  if (ticketsError) return <div>Error: {ticketsError}</div>;
  if (!tickets || tickets.length === 0) return <div>No data available.</div>;

  // console.log("tickets:", tickets);
  // const tickets = tickets.tickets;

  // --- KPIs computed from tickets ---
  const totalTickets = tickets.length;
  const openTickets = tickets.filter((t) => t.status === "Open").length;
  const closedTickets = tickets.filter((t) => t.status === "Closed").length;
  const archivedTickets = tickets.filter((t) => t.status === "Archived").length;
  const activeTickets = totalTickets - archivedTickets;

  // Average resolution time (in hours) from created_at to time_closed (for closed tickets)
  const closedWithResolutionTime = tickets.filter((t) => t.time_closed);
  const avgResolutionTime =
    closedWithResolutionTime.length > 0
      ? Math.round(
          closedWithResolutionTime.reduce((acc, t) => {
            const created = new Date(t.created_at);
            const closed = new Date(t.time_closed);
            return acc + (closed - created) / (1000 * 60 * 60);
          }, 0) / closedWithResolutionTime.length
        )
      : 0;

  // Storage used (fallback if not available)
  const storageUsed = tickets.kpi?.storageUsed || 0;

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
      // value: avgResolutionTime,
      value: 17, // hardcoded for demo
      icon: <Clock size={28} color="#50e3c2" />,
    },
    {
      title: "Storage Used",
      value: storageUsed,
      icon: <HardDrive size={28} color="#a850e3ff" />,
    },
  ];

  // Unique categories
  const categoryLabels = [...new Set(tickets.map((t) => t.category))];
  const categoryDataPoints = categoryLabels.map(
    (cat) => tickets.filter((t) => t.category === cat).length
  );

  // Tickets sorted by created_at for timeline charts
  const ticketsSortedByDate = [...tickets].sort(
    (a, b) => new Date(a.created_at) - new Date(b.created_at)
  );

  // Tickets Over Time labels and cumulative counts
  const dateLabels = ticketsSortedByDate.map((t) => t.created_at.slice(0, 10));
  const ticketCounts = dateLabels.map((_, idx) => idx + 1);

  // Resolution Time Trends - bars show resolution times for closed tickets
  const resolvedTickets = tickets.filter((t) => t.time_closed);
  const resolutionLabels = resolvedTickets.map((t) =>
    t.created_at.slice(0, 10)
  );
  const resolutionDurations = resolvedTickets.map((t) => {
    const created = new Date(t.created_at);
    const closed = new Date(t.time_closed);
    return Math.round((closed - created) / (1000 * 60 * 60));
  });

  // const resolutionDurations = resolvedTickets.map((t) => {
  //   const created = new Date(t.created_at);
  //   const closed = new Date(t.time_closed);
  //   const duration = (closed - created) / (1000 * 60 * 60);

  //   if (duration < 0) {
  //     console.log("Negative resolution time for ticket:", t);
  //   }

  //   return duration < 0 ? 0 : duration; // Correct negative durations to zero
  // });

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
                labels={["Open", "Closed", "Pending", "Archived"]}
                dataPoints={[
                  openTickets,
                  closedTickets,
                  tickets.filter((t) => t.status === "Pending").length,
                  archivedTickets,
                ]}
                chartTitle="Tickets by Status"
                chartLabel="Status"
              />
            </ChartContainer>
            <ChartContainer title="Tickets by Priority">
              <PieChart
                labels={["High", "Medium", "Low"]}
                dataPoints={[
                  tickets.filter((t) => t.priority === "High").length,
                  tickets.filter((t) => t.priority === "Medium").length,
                  tickets.filter((t) => t.priority === "Low").length,
                ]}
                chartTitle="Tickets by Priority"
                chartLabel="Priority"
              />
            </ChartContainer>
            <ChartContainer title="Tickets by Category">
              <BarChart
                labels={categoryLabels}
                dataPoints={categoryDataPoints}
                chartTitle="Tickets by Category"
                chartLabel="Category"
              />
            </ChartContainer>
          </div>
        </div>

        {/* Time-Based Metrics */}
        <div className={styles.chartSection}>
          <h2>Time-Based Metrics</h2>
          <div className={styles.chartRow}>
            <ChartContainer title="Tickets Over Time">
              <LineChart
                labels={dateLabels}
                dataPoints={ticketCounts}
                chartTitle="Tickets Over Time"
                chartLabel="Tickets"
              />
            </ChartContainer>
            <ChartContainer title="Resolution Time Trends">
              <BarChart
                labels={resolutionLabels}
                dataPoints={resolutionDurations}
                chartTitle="Resolution Time Trends (hrs)"
                chartLabel="Hours"
              />
            </ChartContainer>
          </div>
        </div>

        {/* Archive & Trends */}
        <div className={styles.chartSection}>
          <h2>Archive & Trends</h2>
          <div className={styles.chartRow}>
            <ChartContainer title="Archived Tickets Overview">
              <PieChart
                labels={["Archived", "Active"]}
                dataPoints={[archivedTickets, activeTickets]}
                chartTitle="Archived Tickets Overview"
                chartLabel="Archive"
              />
            </ChartContainer>
            <ChartContainer title="Volume Trends">
              <LineChart
                labels={dateLabels}
                dataPoints={ticketCounts}
                chartTitle="Volume Trends"
                chartLabel="Tickets"
              />
            </ChartContainer>
          </div>
        </div>
      </div>

      {/* Table Section */}
      <div className={styles.rpSection}>
        <div className={styles.rpTableSection}>
          <div className={general.tpTable}>
            {/* <TicketTable tickets={tickets} error={error} /> */}
            <DynamicTable
              data={tickets}
              headers={[
                "Ticket No.",
                "Title",
                "Priority",
                "Status",
                "Submit Date",
              ]}
              columns={[
                { key: "ticket_id" },
                { key: "subject" },
                { key: "priority" },
                { key: "status" },
                {
                  key: "submit_date",
                  format: (d) => (d ? format(new Date(d), "yyyy-MM-dd") : ""),
                },
              ]}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
