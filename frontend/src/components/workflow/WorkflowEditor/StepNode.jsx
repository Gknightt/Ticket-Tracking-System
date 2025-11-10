import React, { useCallback } from 'react';
import { Handle, Position, useReactFlow } from 'reactflow';
import styles from './StepNode.module.css';

export default function StepNode({ data, isConnecting }) {
  const { getNode } = useReactFlow();

  const handleNodeClick = useCallback(() => {
    const node = getNode(data.id);
    if (data.onStepClick) {
      data.onStepClick(data);
    }
  }, [data, getNode]);

  return (
    <div className={styles.node} onClick={handleNodeClick}>
      <Handle type="target" position={Position.Top} />
      <div className={styles.nodeContent}>
        <div className={styles.nodeTitle}>{data.label}</div>
        <div className={styles.nodeRole}>{data.role}</div>
        <div className={styles.nodeDescription}>
          {data.description || 'No description'}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
