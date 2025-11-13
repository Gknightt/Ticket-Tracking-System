import React, { useState, useCallback, useEffect } from 'react';
import styles from './SLAWeightEditor.module.css';
import { useWorkflowAPI } from '../../../api/useWorkflowAPI';

export default function SLAWeightEditor({ workflowId, onClose }) {
  const [workflowData, setWorkflowData] = useState(null);
  const [weights, setWeights] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(null);

  const { getWeightData, updateStepWeights } = useWorkflowAPI();

  // Fetch weight data
  useEffect(() => {
    const fetchWeightData = async () => {
      try {
        setLoading(true);
        const data = await getWeightData(workflowId);
        setWorkflowData(data);

        // Initialize weights state
        const weightsMap = {};
        data.steps.forEach(step => {
          weightsMap[step.step_id] = parseFloat(step.weight) || 0.5;
        });
        setWeights(weightsMap);
        setError(null);
      } catch (err) {
        console.error('Error fetching weight data:', err);
        setError(err.message || 'Failed to load weight data');
      } finally {
        setLoading(false);
      }
    };

    fetchWeightData();
  }, [workflowId, getWeightData]);

  const handleWeightChange = useCallback((stepId, newWeight) => {
    setWeights(prev => ({
      ...prev,
      [stepId]: newWeight,
    }));
  }, []);

  const calculateStepSLA = useCallback((stepId, slaValue) => {
    if (!workflowData || !slaValue) return 'N/A';

    const totalWeight = Object.values(weights).reduce((sum, w) => sum + w, 0);
    const stepWeight = weights[stepId] || 0;
    
    if (totalWeight === 0) return 'N/A';

    // Parse duration string (e.g., "432000.0" seconds)
    const seconds = parseFloat(slaValue);
    const stepSeconds = (seconds * stepWeight) / totalWeight;

    return formatDuration(stepSeconds);
  }, [weights, workflowData]);

  const formatDuration = (seconds) => {
    if (isNaN(seconds) || seconds < 0) return 'N/A';

    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);

    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (mins > 0) parts.push(`${mins}m`);

    return parts.length > 0 ? parts.join(' ') : '< 1m';
  };

  const handleSaveWeights = useCallback(async () => {
    try {
      setIsSaving(true);
      setSaveStatus('saving');

      const stepsData = Object.entries(weights).map(([stepId, weight]) => ({
        step_id: parseInt(stepId, 10),
        weight: weight,
      }));

      await updateStepWeights(workflowId, stepsData);
      setSaveStatus('success');
      setTimeout(() => {
        setSaveStatus(null);
      }, 2000);
    } catch (err) {
      console.error('Error saving weights:', err);
      setSaveStatus('error');
      setError(err.message || 'Failed to save weights');
    } finally {
      setIsSaving(false);
    }
  }, [weights, workflowId, updateStepWeights]);

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingSpinner}>
          <div className={styles.spinner}></div>
          <p>Loading weight management data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.errorContainer}>
          <div className={styles.errorIcon}>⚠️</div>
          <p className={styles.errorMessage}>{error}</p>
          <button className={styles.closeBtn} onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h2 className={styles.title}>Weight Management</h2>
          <p className={styles.subtitle}>{workflowData?.workflow_name}</p>
        </div>
        <button className={styles.headerCloseBtn} onClick={onClose}>
          ✕
        </button>
      </div>

      <div className={styles.content}>
        {/* Steps List */}
        <div className={styles.stepsSection}>
          <h3 className={styles.sectionTitle}>Step Weights</h3>
          <div className={styles.stepsList}>
            {workflowData?.steps.map((step) => (
              <div key={step.step_id} className={styles.stepCard}>
                <div className={styles.stepHeader}>
                  <div className={styles.stepInfo}>
                    <div className={styles.stepName}>{step.name}</div>
                    <div className={styles.stepMeta}>{step.role_name} • Step {step.order}</div>
                  </div>
                  <div className={styles.stepWeight}>{(parseFloat(weights[step.step_id]) || 0.5).toFixed(2)}</div>
                </div>

                <div className={styles.sliderContainer}>
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.01"
                    value={parseFloat(weights[step.step_id]) || 0.5}
                    onChange={(e) =>
                      handleWeightChange(step.step_id, parseFloat(e.target.value))
                    }
                    className={styles.slider}
                  />
                </div>

                {/* SLA Breakdown */}
                <div className={styles.slaBreakdown}>
                  {[
                    { label: 'Urgent', value: workflowData?.slas.urgent_sla },
                    { label: 'High', value: workflowData?.slas.high_sla },
                    { label: 'Medium', value: workflowData?.slas.medium_sla },
                    { label: 'Low', value: workflowData?.slas.low_sla },
                  ].map((sla) => (
                    <div key={sla.label} className={styles.slaItem}>
                      <span className={styles.slaLabel}>{sla.label}</span>
                      <span className={styles.slaValue}>
                        {calculateStepSLA(step.step_id, sla.value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* SLA Reference */}
        <div className={styles.referenceSection}>
          <h3 className={styles.sectionTitle}>Total SLAs</h3>
          <div className={styles.slaGrid}>
            {[
              { label: 'Urgent', value: workflowData?.slas.urgent_sla },
              { label: 'High', value: workflowData?.slas.high_sla },
              { label: 'Medium', value: workflowData?.slas.medium_sla },
              { label: 'Low', value: workflowData?.slas.low_sla },
            ].map((sla) => (
              <div key={sla.label} className={styles.slaCard}>
                <div className={styles.slaCardLabel}>{sla.label}</div>
                <div className={styles.slaCardValue}>{formatDuration(parseFloat(sla.value))}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className={styles.footer}>
        <div className={styles.saveStatus}>
          {saveStatus === 'saving' && (
            <span className={styles.savingText}>
              <span className={styles.spinner}></span>
              Saving...
            </span>
          )}
          {saveStatus === 'success' && (
            <span className={styles.successText}>✓ Saved successfully</span>
          )}
          {saveStatus === 'error' && (
            <span className={styles.errorText}>✕ Error saving weights</span>
          )}
        </div>

        <div className={styles.actions}>
          <button
            className={styles.cancelBtn}
            onClick={onClose}
            disabled={isSaving}
          >
            Cancel
          </button>
          <button
            className={styles.saveBtn}
            onClick={handleSaveWeights}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Weights'}
          </button>
        </div>
      </div>
    </div>
  );
}
