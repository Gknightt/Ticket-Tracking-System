// styles
import styles from "./admin-dashboard.module.css";

// components
import AdminNav from "../../../components/navigation/AdminNav";
import TicketCard from "./components/TicketCard";
import QuickAction from "./components/QuickAction";

// charts
import ChartComponent from "./charts/ChartCompoent";
import LineChart from './charts/LineChart';
import BarChart from './charts/BarChart';
import PieChart from './charts/PieChart';
import RadarChart from './charts/RadarChart';

export default function AdminDashboard() {
  return (
    <>
      <AdminNav />
      <main className={styles.adminDashboardPage}>
        <section className={styles.adpHeader}>
          <h1>Dashboard</h1>
        </section>
        <section className={styles.adpBody}>
          <div className={styles.adpCardSection}>
            <div className={styles.adpWrapper}>
              <div className={styles.adpLeftRight}>
                <div className={styles.adpLeft}>
                  <TicketCard number="9" label="New Tickets" />
                  <TicketCard number="9" label="Open Tickets" />
                </div>
                <div className={styles.adpMid}>
                  <TicketCard number="9" label="Resolved Tickets" />
                  <TicketCard number="9" label="On Hold Tickets" />
                </div>
                <div className={styles.adpRight}>
                  <TicketCard number="9" label="In Progress" />
                  <TicketCard number="9" label="Rejected Tickets" />
                </div>
              </div>
              <div className={styles.adpSide}>
                <TicketCard number="9" label="Critical" />
              </div>
            </div>
          </div>
          <div className={styles.adpContentSection}>
            <div className={styles.adpVisuals}>
              <h2>Charts</h2>
              <LineChart />
            </div>
            <div className={styles.adpQuickActionSection}>
              <h2>Quick Actions</h2>
              <div className={styles.adpQuicActions}>
                <QuickAction />
              </div>
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
