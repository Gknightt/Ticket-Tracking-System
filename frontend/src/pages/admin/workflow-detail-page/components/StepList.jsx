import React from 'react';
import styles from '../WorkflowEditor.module.css';

export default function StepList({ steps, transitions, getRoleName, getActionName, getStepName, handleEditStep, removeStep }) {
  return (
    <div className={styles.stepsList}>
      {steps.map(step => {
        const outgoing = transitions.filter(t => t.from_step_id === step.step_id);
        return (
          <div key={step.step_id} className={styles.stepCard}>
            <div className={styles.stepHeader}>
              <div>
                <h3 className={styles.stepTitle}>{step.order}. {step.name}</h3>
                <p className={styles.stepRole}>Role: {getRoleName(step.role_id)}</p>
              </div>
              <div className={styles.buttonGroup}>
                <button onClick={() => handleEditStep(step)} className={styles.editButton} >Edit</button>
                <button onClick={() => removeStep(step.step_id)} className={styles.removeButton}>Remove</button>
              </div>
            </div>
            <div className={styles.transitionsList}>
              {outgoing.map(t => (
                <div key={t.transition_id} className={styles.transitionItem}>
                  {getActionName(t.action_id)} → {getStepName(t.to_step_id)}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
