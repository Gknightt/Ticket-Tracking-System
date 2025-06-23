import React from 'react';
import { useParams } from 'react-router-dom';
import styles from '../WorkflowEditor.module.css';

import StepForm from './StepForm';
import NewWorkflowVisualizer from "../../../../components/workflow/NewWorkflowVisualizer";
import TransitionModal from './TransitionModal';
import StepModal from './StepModal';
import StepList from './StepList';
import useWorkflowEditorState from './useWorkflowEditorState';
import TransitionList from './TransitionList';
import AddTransitionForm from './AddTransitionForm';

export default function WorkflowEditor2() {
  const { uuid } = useParams();
  const state = useWorkflowEditorState(uuid);

  const { workflow, loading, error } = state;

  if (loading) return <div className={styles.loading}>Loading workflow...</div>;
  if (error) return <div className={styles.error}>Error: {error}</div>;
  if (!workflow) return <div className={styles.loading}>No workflow found.</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <NewWorkflowVisualizer workflowId={uuid} />
        <h1 className={styles.title}>{workflow.name}</h1>
        <p className={styles.description}>{workflow.description}</p>
        <span className={styles.statusBadge}>{workflow.status}</span>
      </div>

      <div className={styles.grid}>
        <div className={styles.section}>
          <StepForm {...state} />
          <StepList {...state} />
        </div>
        <div className={styles.section}>
        <TransitionList {...state} />
        <AddTransitionForm  {...state}/>
      </div>

      </div>

      <StepModal {...state} />
      <TransitionModal {...state} />
    </div>
  );
}
