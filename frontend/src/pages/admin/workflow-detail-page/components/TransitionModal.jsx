import React from 'react';
import styles from '../WorkflowEditor.module.css';

export default function TransitionModal({
  editTransitionModal,
  setEditTransitionModal,
  updateTransition,
  steps,
  refetch
}) {
  if (!editTransitionModal.isOpen) return null;

  const updateField = (field, value) => {
    setEditTransitionModal(prev => ({
      ...prev,
      transition: { ...prev.transition, [field]: value },
    }));
  };

  const handleSave = async () => {
    const t = editTransitionModal.transition;
    if (!t.transition_id || !t.from_step_id || !t.to_step_id || !t.action_name) return;

    await updateTransition(t.transition_id, {
      from_step_id: t.from_step_id,
      to_step_id: t.to_step_id,
      action_name: t.action_name,
    });
    await refetch();
    setEditTransitionModal({ isOpen: false, transition: null });
  };

  return (
    <div className={styles.modalOverlay}>
      <div className={styles.modal}>
        <div className={styles.modalHeader}>
          <h3 className={styles.modalTitle}>Edit Transition</h3>
          <button
            onClick={() => setEditTransitionModal({ isOpen: false, transition: null })}
            className={styles.modalCloseButton}
          >×</button>
        </div>

        <div className={styles.modalContent}>
          <div className={styles.formField}>
            <label className={styles.label}>From Step</label>
            <select
              value={editTransitionModal.transition?.from_step_id || ''}
              onChange={(e) => updateField('from_step_id', e.target.value)}
              className={styles.select}
            >
              <option value="">Select step</option>
              {steps.map(step => (
                <option key={step.step_id} value={step.step_id}>{step.name}</option>
              ))}
            </select>
          </div>

          <div className={styles.formField}>
            <label className={styles.label}>To Step</label>
            <select
              value={editTransitionModal.transition?.to_step_id || ''}
              onChange={(e) => updateField('to_step_id', e.target.value)}
              className={styles.select}
            >
              <option value="">End workflow</option>
              {steps
                .filter(step => step.step_id !== editTransitionModal.transition?.from_step_id)
                .map(step => (
                  <option key={step.step_id} value={step.step_id}>{step.name}</option>
              ))}
            </select>
          </div>

          <div className={styles.formField}>
            <label className={styles.label}>Action Name</label>
            <input
              type="text"
              value={editTransitionModal.transition?.action_name || ''}
              onChange={(e) => updateField('action_name', e.target.value)}
              className={styles.input}
              placeholder="Action name"
            />
          </div>
        </div>

        <div className={styles.modalFooter}>
          <button
            onClick={() => setEditTransitionModal({ isOpen: false, transition: null })}
            className={styles.cancelButton}
          >
            Cancel
          </button>
          <button onClick={handleSave} className={styles.saveButton}>
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}
