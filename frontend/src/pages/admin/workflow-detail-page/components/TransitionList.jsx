import React from 'react';
import styles from '../WorkflowEditor.module.css';

export default function TransitionList({
  transitions,
  steps,
  newTransition,
  setNewTransition,
  getStepName,
  getActionName,
  handleEditTransition,
  removeTransition,
  handleCreateTransition,
}) {
  return (
    <div className={styles.section}>
      <h2 className={styles.sectionTitle}>Workflow Flow</h2>

      <div className={styles.transitionsSection}>
        {transitions.map((transition) => (
          <div key={transition.transition_id} className={styles.transitionCard}>
            <div className={styles.transitionHeader}>
              <div>
                <div className={styles.transitionFlow}>
                  <span className={styles.transitionStep}>{getStepName(transition.from_step_id)}</span>
                  <span className={styles.transitionArrow}>→</span>
                  <span className={styles.transitionStep}>{getStepName(transition.to_step_id)}</span>
                </div>
                <div className={styles.transitionAction}>
                  Action: {getActionName(transition.action_id)}
                </div>
              </div>
              <div className={styles.buttonGroup}>
                <button onClick={() => handleEditTransition(transition)} className={styles.editButton}>
                  Edit
                </button>
                <button onClick={() => removeTransition(transition.transition_id)} className={styles.removeButton}>
                  Remove
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* <div className={styles.addTransitionForm}>
        <h3 className={styles.formTitle}>Add New Flow</h3>
        <div className={styles.formFields}>
          <div className={styles.formField}>
            <label className={styles.label}>From Step</label>
            <select
              value={newTransition.from}
              onChange={(e) => setNewTransition({ ...newTransition, from: e.target.value || null })}
              className={styles.select}
            >
              <option value="">Select Step</option>
              {steps.map((step) => (
                <option key={step.step_id} value={step.step_id}>
                  {step.description}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.formField}>
            <label className={styles.label}>To Step</label>
            <select
              value={newTransition.to}
              onChange={(e) => setNewTransition({ ...newTransition, to: e.target.value })}
              className={styles.select}
            >
              <option value="">End workflow</option>
              {steps
                .filter((step) => step.step_id !== newTransition.from)
                .map((step) => (
                  <option key={step.step_id} value={step.step_id}>
                    {step.description}
                  </option>
                ))}
            </select>
          </div>

          <div className={styles.formField}>
            <label className={styles.label}>Action Name</label>
            <input
              type="text"
              value={newTransition.actionName}
              onChange={(e) => setNewTransition({ ...newTransition, actionName: e.target.value })}
              placeholder="Enter action name"
              className={styles.input}
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.label}>Action Description</label>
            <input
              type="text"
              value={newTransition.actionDescription}
              onChange={(e) => setNewTransition({ ...newTransition, actionDescription: e.target.value })}
              placeholder="Enter action description"
              className={styles.input}
            />
          </div>

          <button onClick={handleCreateTransition} className={styles.addTransitionButton}>
            Add Flow
          </button>
        </div>
      </div> */}
    </div>
  );
}
