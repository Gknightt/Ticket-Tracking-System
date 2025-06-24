// components/WorkflowTracker.jsx
import React from "react";
import styles from "./WorkflowTrackerBase.module.css";

const statusIcons = {
  done: "✅",
  active: "🔥",
  pending: "⏳",
};

export default function WorkflowVisualizer2({ workflowData }) {
  if (!workflowData) {
    return <div className={styles.loading}>Loading tracker...</div>;
  }

  const renderConnector = (index, currentStatus, nextStatus) => {
    if (index === workflowData.nodes.length - 1) return null;
    
    const isActive = currentStatus === 'done' || (currentStatus === 'active' && nextStatus !== 'done');
    
    return (
      <div 
        className={`${styles.connector} ${isActive ? styles.active : ''}`}
        key={`connector-${index}`}
      />
    );
  };

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Workflow Progress</h3>

      <div className={styles.workflow}>
        {workflowData.nodes.map((node, index) => {
          const nextNode = workflowData.nodes[index + 1];
          
          return (
            <React.Fragment key={node.id}>
              <div className={styles.nodeContainer}>
                <div className={`${styles.circle} ${styles[node.status]}`}>
                  {statusIcons[node.status] || "❔"}
                </div>
                
                <div className={styles.nodeInfo}>
                  <div className={styles.nodeLabel}>{node.label}</div>
                  <div className={styles.nodeRole}>
                    <strong>{node.role}</strong>
                  </div>
                  {/* {node.instruction && (
                    <div className={styles.nodeInstruction}>
                      📘 {node.instruction}
                    </div>
                  )} */}
                </div>
              </div>
              
              {renderConnector(index, node.status, nextNode?.status)}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}