import { useState, useEffect } from "react";
import { X, ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import styles from "./drilldown-modal.module.css";

/**
 * DrilldownModal - Displays detailed records when drilling down into analytics
 * 
 * @param {boolean} isOpen - Whether the modal is visible
 * @param {function} onClose - Callback to close the modal
 * @param {string} title - Modal title
 * @param {object} data - Drilldown response data with pagination info
 * @param {array} columns - Column definitions [{ key, label, render? }]
 * @param {function} onPageChange - Callback when page changes (receives page number)
 * @param {boolean} loading - Loading state
 * @param {function} onRowClick - Optional callback when row is clicked
 */
export default function DrilldownModal({
  isOpen,
  onClose,
  title,
  data,
  columns = [],
  onPageChange,
  loading = false,
  onRowClick,
}) {
  const [currentPage, setCurrentPage] = useState(1);

  // Reset page when data changes
  useEffect(() => {
    if (data?.page) {
      setCurrentPage(data.page);
    }
  }, [data?.page]);

  if (!isOpen) return null;

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= (data?.total_pages || 1)) {
      setCurrentPage(newPage);
      if (onPageChange) {
        onPageChange(newPage);
      }
    }
  };

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Get items array from data - handle different response structures
  const items = data?.tickets || data?.tasks || data?.task_items || data?.transfers || [];
  const totalCount = data?.total_count || 0;
  const totalPages = data?.total_pages || 1;
  const pageSize = data?.page_size || 20;

  // Generate page numbers for pagination
  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    
    if (end - start < maxVisible - 1) {
      start = Math.max(1, end - maxVisible + 1);
    }

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    return pages;
  };

  return (
    <div className={styles.modalBackdrop} onClick={handleBackdropClick}>
      <div className={styles.modalContent}>
        {/* Header */}
        <div className={styles.modalHeader}>
          <h2 className={styles.modalTitle}>{title}</h2>
          <div className={styles.headerInfo}>
            <span className={styles.totalCount}>{totalCount} records</span>
            <button className={styles.closeBtn} onClick={onClose}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Filters Applied */}
        {data?.filters_applied && Object.keys(data.filters_applied).some(k => data.filters_applied[k]) && (
          <div className={styles.filtersBar}>
            <span className={styles.filtersLabel}>Filters:</span>
            {Object.entries(data.filters_applied).map(([key, value]) => 
              value && (
                <span key={key} className={styles.filterTag}>
                  {key.replace(/_/g, ' ')}: {value}
                </span>
              )
            )}
          </div>
        )}

        {/* Content */}
        <div className={styles.modalBody}>
          {loading ? (
            <div className={styles.loadingState}>
              <div className={styles.spinner}></div>
              <p>Loading...</p>
            </div>
          ) : items.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No records found</p>
            </div>
          ) : (
            <div className={styles.tableWrapper}>
              <table className={styles.dataTable}>
                <thead>
                  <tr>
                    {columns.map((col) => (
                      <th key={col.key}>{col.label}</th>
                    ))}
                    {onRowClick && <th className={styles.actionCol}>Action</th>}
                  </tr>
                </thead>
                <tbody>
                  {items.map((item, idx) => (
                    <tr 
                      key={item.task_id || item.task_item_id || idx}
                      className={onRowClick ? styles.clickableRow : ''}
                      onClick={() => onRowClick && onRowClick(item)}
                    >
                      {columns.map((col) => (
                        <td key={col.key}>
                          {col.render ? col.render(item[col.key], item) : formatValue(item[col.key])}
                        </td>
                      ))}
                      {onRowClick && (
                        <td className={styles.actionCol}>
                          <ExternalLink size={16} className={styles.actionIcon} />
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && !loading && (
          <div className={styles.pagination}>
            <button
              className={styles.pageBtn}
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
            >
              <ChevronLeft size={18} />
            </button>
            
            {getPageNumbers().map((pageNum) => (
              <button
                key={pageNum}
                className={`${styles.pageBtn} ${pageNum === currentPage ? styles.active : ''}`}
                onClick={() => handlePageChange(pageNum)}
              >
                {pageNum}
              </button>
            ))}
            
            <button
              className={styles.pageBtn}
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              <ChevronRight size={18} />
            </button>
            
            <span className={styles.pageInfo}>
              Page {currentPage} of {totalPages}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Format value for display
 */
function formatValue(value) {
  if (value === null || value === undefined) return '-';
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  
  // Check if it's a date string
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
    return new Date(value).toLocaleString();
  }
  
  // Check if it's an array
  if (Array.isArray(value)) {
    return value.join(', ') || '-';
  }
  
  return String(value);
}

/**
 * Pre-defined column configurations for common drilldown types
 */
export const DRILLDOWN_COLUMNS = {
  tickets: [
    { key: 'ticket_number', label: 'Ticket #' },
    { key: 'subject', label: 'Subject' },
    { key: 'status', label: 'Status', render: (val) => <StatusBadge status={val} /> },
    { key: 'priority', label: 'Priority', render: (val) => <PriorityBadge priority={val} /> },
    { key: 'workflow_name', label: 'Workflow' },
    { key: 'created_at', label: 'Created', render: (val) => formatDate(val) },
    { key: 'sla_status', label: 'SLA', render: (val) => <SLABadge status={val} /> },
  ],
  ticketsSimple: [
    { key: 'ticket_number', label: 'Ticket #' },
    { key: 'subject', label: 'Subject' },
    { key: 'status', label: 'Status', render: (val) => <StatusBadge status={val} /> },
    { key: 'priority', label: 'Priority', render: (val) => <PriorityBadge priority={val} /> },
    { key: 'created_at', label: 'Created', render: (val) => formatDate(val) },
  ],
  sla: [
    { key: 'ticket_number', label: 'Ticket #' },
    { key: 'subject', label: 'Subject' },
    { key: 'priority', label: 'Priority', render: (val) => <PriorityBadge priority={val} /> },
    { key: 'status', label: 'Status', render: (val) => <StatusBadge status={val} /> },
    { key: 'target_resolution', label: 'Target', render: (val) => formatDate(val) },
    { key: 'sla_status', label: 'SLA', render: (val) => <SLABadge status={val} /> },
    { key: 'time_remaining_hours', label: 'Remaining (hrs)' },
    { key: 'time_overdue_hours', label: 'Overdue (hrs)' },
  ],
  taskItems: [
    { key: 'ticket_number', label: 'Ticket #' },
    { key: 'subject', label: 'Subject' },
    { key: 'user_name', label: 'Assigned To' },
    { key: 'status', label: 'Status', render: (val) => <StatusBadge status={val} /> },
    { key: 'origin', label: 'Origin' },
    { key: 'assigned_on', label: 'Assigned', render: (val) => formatDate(val) },
    { key: 'step_name', label: 'Step' },
  ],
  userTasks: [
    { key: 'ticket_number', label: 'Ticket #' },
    { key: 'subject', label: 'Subject' },
    { key: 'status', label: 'Status', render: (val) => <StatusBadge status={val} /> },
    { key: 'origin', label: 'Origin' },
    { key: 'assigned_on', label: 'Assigned', render: (val) => formatDate(val) },
    { key: 'time_to_action_hours', label: 'Action Time (hrs)' },
    { key: 'sla_status', label: 'SLA', render: (val) => <SLABadge status={val} /> },
  ],
  workflows: [
    { key: 'ticket_number', label: 'Ticket #' },
    { key: 'subject', label: 'Subject' },
    { key: 'status', label: 'Status', render: (val) => <StatusBadge status={val} /> },
    { key: 'current_step', label: 'Current Step' },
    { key: 'created_at', label: 'Created', render: (val) => formatDate(val) },
  ],
  transfers: [
    { key: 'ticket_number', label: 'Ticket #' },
    { key: 'from_user', label: 'From' },
    { key: 'to_user', label: 'To' },
    { key: 'origin', label: 'Type' },
    { key: 'step_name', label: 'Step' },
    { key: 'transferred_at', label: 'Date', render: (val) => formatDate(val) },
  ],
};

// Helper components for rendering badges
function StatusBadge({ status }) {
  const statusColors = {
    'pending': '#f5a623',
    'in progress': '#4a90e2',
    'completed': '#7ed321',
    'new': '#9b9b9b',
    'resolved': '#7ed321',
    'escalated': '#e74c3c',
    'reassigned': '#f5a623',
    'on_hold': '#9b9b9b',
    'cancelled': '#e74c3c',
  };
  const color = statusColors[status?.toLowerCase()] || '#9b9b9b';
  return (
    <span style={{ 
      color, 
      fontWeight: 500,
      textTransform: 'capitalize' 
    }}>
      {status || '-'}
    </span>
  );
}

function PriorityBadge({ priority }) {
  const priorityColors = {
    'critical': '#e74c3c',
    'high': '#f5a623',
    'medium': '#4a90e2',
    'low': '#7ed321',
  };
  const color = priorityColors[priority?.toLowerCase()] || '#9b9b9b';
  return (
    <span style={{ 
      color, 
      fontWeight: 500,
      textTransform: 'capitalize' 
    }}>
      {priority || '-'}
    </span>
  );
}

function SLABadge({ status }) {
  const slaColors = {
    'met': '#7ed321',
    'on_track': '#4a90e2',
    'at_risk': '#e74c3c',
    'breached': '#e74c3c',
    'no_sla': '#9b9b9b',
  };
  const slaLabels = {
    'met': 'Met',
    'on_track': 'On Track',
    'at_risk': 'At Risk',
    'breached': 'Breached',
    'no_sla': 'No SLA',
  };
  const color = slaColors[status] || '#9b9b9b';
  return (
    <span style={{ 
      color, 
      fontWeight: 500 
    }}>
      {slaLabels[status] || status || '-'}
    </span>
  );
}

function formatDate(value) {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return value;
  }
}
