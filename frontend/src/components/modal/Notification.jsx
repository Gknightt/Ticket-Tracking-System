// react
import { useEffect, useState } from "react";

// hook
import { useNotifications } from "../../api/useNotification";

// styles
import styles from "./notification.module.css";

import { formatDistanceToNow, parseISO } from "date-fns";

export default function Notification({ closeNotifAction }) {
  const {
    notifications,
    loading,
    error,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
  } = useNotifications();

  // Active tab: show 'unread' by default
  const [activeTab, setActiveTab] = useState("unread");

  // Prefetch all lists on mount so counts are available and tabs are responsive
  useEffect(() => {
    fetchNotifications("unread");
    fetchNotifications("read");
    fetchNotifications("all");
  }, [fetchNotifications]);

  const handleMarkAsRead = async (id) => {
    await markAsRead(id);
    // hook already refreshes lists after marking; no extra fetch needed here
  };

  const handleClearAll = async () => {
    await markAllAsRead();
    // hook already refreshes lists after marking all; no extra fetch needed here
  };

  // Normalize list to ensure it's always an array before mapping
  const rawList = notifications?.[activeTab] || [];
  const list = Array.isArray(rawList) ? rawList : [];
  if (rawList && !Array.isArray(rawList)) {
    // eslint-disable-next-line no-console
    console.warn(
      "Notifications list is not an array, falling back to empty array",
      rawList
    );
  }

  const unreadCount = Array.isArray(notifications?.unread)
    ? notifications.unread.length
    : 0;
  const readCount = Array.isArray(notifications?.read)
    ? notifications.read.length
    : 0;
  const allCount = Array.isArray(notifications?.all)
    ? notifications.all.length
    : 0;

  // Function to format date
  const formatDate = (dateString) => {
    const date = parseISO(dateString); // Parse the ISO date string to Date object
    return formatDistanceToNow(date, { addSuffix: true }); // e.g. "2 hours ago"
  };

  return (
    <div
      className={styles.nOverlayWrapper}
      onClick={() => closeNotifAction(false)}
    >
      <div
        className={styles.notificationModalCont}
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.nHeader}>
          <h2>Notifications</h2>
          <div className={styles.nHeaderRight}>
            {/* <div className={styles.tabGroup}>
              <button
                className={
                  activeTab === "unread" ? styles.activeTab : styles.tab
                }
                onClick={() => setActiveTab("unread")}
              >
                Unread ({unreadCount})
              </button>
              <button
                className={activeTab === "read" ? styles.activeTab : styles.tab}
                onClick={() => setActiveTab("read")}
              >
                Read ({readCount})
              </button>
              <button
                className={activeTab === "all" ? styles.activeTab : styles.tab}
                onClick={() => setActiveTab("all")}
              >
                All ({allCount})
              </button>
            </div> */}
            <div className={styles.tabGroup}>
              <button
                className={
                  activeTab === "unread" ? styles.activeTab : styles.tab
                }
                onClick={() => setActiveTab("unread")}
                title="Unread"
              >
                <i className="fa-solid fa-envelope"></i> ({unreadCount})
              </button>

              <button
                className={activeTab === "read" ? styles.activeTab : styles.tab}
                onClick={() => setActiveTab("read")}
                title="Read"
              >
                <i className="fa-solid fa-envelope-open"></i> ({readCount})
              </button>

              <button
                className={activeTab === "all" ? styles.activeTab : styles.tab}
                onClick={() => setActiveTab("all")}
                title="All"
              >
                <i className="fa-solid fa-bell"></i> ({allCount})
              </button>
            </div>

            {activeTab === "unread" && unreadCount > 0 && (
              <button className={styles.nClearButton} onClick={handleClearAll}>
                Mark All Read
              </button>
            )}
          </div>
        </div>

        {loading && <div className={styles.emptyState}>Loading...</div>}
        {error && <div className={styles.emptyState}>{error}</div>}

        <div className={styles.nList}>
          {!loading && !error && list.length === 0 ? (
            <p className={styles.emptyState}>No notifications.</p>
          ) : (
            list.map((n) => (
              <div key={n.id} className={styles.nItem}>
                <div className={styles.nUserAvatar}>
                  <img
                    className={styles.userAvatar}
                    // src={
                    //   n.avatar ||
                    //   "https://i.pinimg.com/736x/e6/50/7f/e6507f42d79520263d8d952633cedcf2.jpg"
                    // }
                    src="/map-logo.png"
                    alt="User Avatar"
                  />
                </div>
                <div className={styles.nContent}>
                  <h3>{n.subject || "no subject"}</h3>
                  <p>{n.message}</p>
                  {/* <span className={styles.nTime}>
                    {n.created_at || "Just now"}
                  </span> */}
                  <span className={styles.nTime}>
                    {n.created_at ? formatDate(n.created_at) : "Just now"}
                  </span>
                </div>
                <div
                  className={styles.nDeleteButton}
                  onClick={() => handleMarkAsRead(n.id)}
                >
                  <i className="fa-solid fa-trash"></i>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
