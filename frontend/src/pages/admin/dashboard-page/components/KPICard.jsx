// style
import styles from "./kpi-card.module.css";

export default function KPICard(props) {
  const statusClassMap = {
    "New Tickets": styles.newTickets,
    Critical: styles.critical,
    High: styles.high,
    Medium: styles.medium,
    Low: styles.low,
  };

  return (
    <div
      className={`${styles.statusCard} ${statusClassMap[props.label] || ""}`}
    >
      <div className={styles.contentWrapper}>
        <div
          className={`${styles.statusNumber} ${
            statusClassMap[props.label] || ""
          }`}
        >
          {props.number}
        </div>
        <div className={styles.statusTitle}>{props.label}</div>
      </div>
    </div>
  );
}
