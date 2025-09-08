import { useState, useEffect } from "react";
import useUserTickets from "../../api/useUserTickets";
import useTicketsFetcher from "../../api/useTicketsFetcher";

// components
import AdminNav from "../../components/navigation/AdminNav";
import PieChart from "../../components/charts/PieChart";
import BarChart from "../../components/charts/BarChart";
import LineChart from "../../components/charts/LineChart";
import DoughnutChart from "../../components/charts/DoughnutChart";
import ChartContainer from "../../components/charts/ChartContainer";

// table
import TicketTable from "../../tables/admin/TicketTable";
import DynamicTable from "../../tables/components/DynamicTable";

// styles
import styles from "./report.module.css";
import general from "../../style/general.module.css";

// lucide icons
import { Ticket, FolderOpen, CheckCircle, Clock } from "lucide-react";

export default function Report() {
  // Fetch user tickets
  const { fetchTickets, tickets, loading, error } = useTicketsFetcher();

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  // logging allTickets for debugging
  // console.log(allTickets);F

  // State for active tabs
  const [activeTab, setActiveTab] = useState("ticket");

  const handleTabClick = (e, tab) => {
    e.preventDefault(); // Prevent the default anchor behavior
    setActiveTab(tab); // Set the active tab state
  };

  const kpiCardData = [
    {
      title: "Total Tickets",
      value: 1200,
      icon: <Ticket size={28} color="#4a90e2" />,
    },
    {
      title: "Open Tickets",
      value: 300,
      icon: <FolderOpen size={28} color="#f5a623" />,
    },
    {
      title: "Closed Tickets",
      value: 900,
      icon: <CheckCircle size={28} color="#7ed321" />,
    },
    {
      title: "Avg. Resolution Time",
      value: "2 days",
      icon: <Clock size={28} color="#50e3c2" />,
    },
  ];

  return (
    <>
      <AdminNav />
      <main className={styles.reportPage}>
        <section className={styles.rpHeader}>
          <h1>Reporting and Analytics</h1>
          {/* <p>View and analyze ticket data</p> */}
        </section>

        <section className={styles.rpBody}>
          {/* Tabs */}
          <div className={styles.rpTabs}>
            {["ticket", "workflow", "agent", "integration"].map((tab) => (
              <a
                key={tab}
                href="#"
                onClick={(e) => handleTabClick(e, tab)}
                className={`${styles.rpTabLink} ${
                  activeTab === tab ? styles.active : ""
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </a>
            ))}
          </div>

          {activeTab === "ticket" && (
            <div className={styles.rpTicketTabSection}>
              {/* KPI */}
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

              {/* chartsGrid - Ticket*/}
              <div className={styles.chartsGrid}>
                {/* Ticket Analytics Section */}
                <div className={styles.chartSection}>
                  <h2>Ticket Analytics</h2>
                  <div className={styles.chartRow}>
                    <ChartContainer title="Tickets by Status">
                      <PieChart />
                    </ChartContainer>
                    <ChartContainer title="Tickets by Priority">
                      <PieChart />
                    </ChartContainer>
                    <ChartContainer title="Tickets by Category">
                      <BarChart />
                    </ChartContainer>
                  </div>
                </div>

                {/* Time-Based Metrics */}
                <div className={styles.chartSection}>
                  <h2>Time-Based Metrics</h2>
                  <div className={styles.chartRow}>
                    <ChartContainer title="Tickets Over Time">
                      <LineChart />
                    </ChartContainer>
                    <ChartContainer title="Resolution Time Trends">
                      <BarChart />
                    </ChartContainer>
                  </div>
                </div>
                {/* Archive & Trends */}
                <div className={styles.chartSection}>
                  <h2>Archive & Trends</h2>
                  <div className={styles.chartRow}>
                    <ChartContainer title="Archived Tickets Overview">
                      <PieChart />
                    </ChartContainer>
                    <ChartContainer title="Volume Trends">
                      <LineChart />
                    </ChartContainer>
                  </div>
                </div>
              </div>

              {/* Table Section */}
              <div className={styles.rpSection}>
                <div className={styles.rpTableSection}>
                  <div className={general.tpTable}>
                    {loading && (
                      <div className={styles.loaderOverlay}>
                        <div className={styles.loader}></div>
                      </div>
                    )}
                    <TicketTable tickets={tickets} error={error} />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* chartsGrid - Workflow */}
          {activeTab === "workflow" && (
            <div className={styles.chartsGrid}>
              {/* Workflow Analytics */}
              <div className={styles.chartSection}>
                <h2>Workflow Analytics</h2>
                <div className={styles.chartRow}>
                  <ChartContainer title="Workflow Usage">
                    <BarChart />
                  </ChartContainer>
                  <ChartContainer title="Workflow Completion Rates">
                    <BarChart />
                  </ChartContainer>
                  <ChartContainer title="Average Time per Workflow Step">
                    <LineChart />
                  </ChartContainer>
                </div>
              </div>
            </div>
          )}

          {/* chartsGrid - Agent*/}
          {activeTab === "agent" && (
            <div className={styles.chartsGrid}>
              {/* Agent Performance */}
              <div className={styles.chartSection}>
                <h2>Agent Performance</h2>
                <div className={styles.chartRow}>
                  <ChartContainer title="Tickets Handled per Agent">
                    <DoughnutChart />
                  </ChartContainer>
                  <ChartContainer title="Average Response Time by Agent">
                    <BarChart />
                  </ChartContainer>
                </div>
              </div>

              {/* User & Department Insights */}
              <div className={styles.chartSection}>
                <h2>User & Department Insights</h2>
                <div className={styles.chartRow}>
                  <ChartContainer title="Tickets by Department">
                    <PieChart />
                  </ChartContainer>
                  <ChartContainer title="Top Recurring Issues">
                    <LineChart />
                  </ChartContainer>
                </div>
              </div>
            </div>
          )}

          {/* Integration */}
          {activeTab === "integration" && (
            <div className={styles.chartsGrid}>
              <div className={styles.chartSection}>
                <h2>Integration Metrics</h2>
                <div className={styles.chartRow}>
                  <ChartContainer title="Status of Integrations">
                    <PieChart />
                  </ChartContainer>
                  <ChartContainer title="Response Times by Integration">
                    <LineChart />
                  </ChartContainer>
                  <ChartContainer title="Error Rates by Integration">
                    <BarChart />
                  </ChartContainer>
                </div>
              </div>
              <div className={styles.chartRow}>
                <div className={styles.chartSection}>
                  <h2>API Logs</h2>
                  <DynamicTable />
                </div>
                <div className={styles.chartSection}>
                  <h2>Integration Logs</h2>
                  <DynamicTable />
                </div>
              </div>
            </div>
          )}
          
        </section>
      </main>
    </>
  );
}
