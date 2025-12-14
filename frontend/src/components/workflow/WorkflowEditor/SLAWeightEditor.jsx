import React, { useState, useCallback, useEffect } from 'react';
import { X, Info } from 'lucide-react';
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
        onClose();
      }, 1000);
    } catch (err) {
      console.error('Error saving weights:', err);
      setSaveStatus('error');
      setError(err.message || 'Failed to save weights');
    } finally {
      setIsSaving(false);
    }
  }, [weights, workflowId, updateStepWeights, onClose]);

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-8">
          <div className="flex items-center justify-center gap-3">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-gray-600">Loading weight management data...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !workflowData) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-8">
          <div className="text-center">
            <div className="text-4xl mb-4">⚠️</div>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  const totalWeight = Object.values(weights).reduce((sum, w) => sum + w, 0);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col">
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">SLA Time Distribution</h2>
            <p className="text-sm text-gray-600 mt-1">
              {workflowData?.workflow_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        <div className="p-6 flex-1 overflow-y-auto">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 flex gap-3">
            <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900">
              <p>Weights determine the relative time allocation for each step.</p>
              <p className="mt-1">Higher weights = more time allocated to that step.</p>
            </div>
          </div>

          {/* SLA Reference */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-900 mb-3">Total SLAs by Priority</h3>
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: 'Urgent', value: workflowData?.slas?.urgent_sla, color: 'red' },
                { label: 'High', value: workflowData?.slas?.high_sla, color: 'orange' },
                { label: 'Medium', value: workflowData?.slas?.medium_sla, color: 'yellow' },
                { label: 'Low', value: workflowData?.slas?.low_sla, color: 'green' },
              ].map((sla) => (
                <div key={sla.label} className="bg-gray-50 rounded-lg p-3 text-center">
                  <div className="text-xs text-gray-600">{sla.label}</div>
                  <div className="text-sm font-medium text-gray-900">{formatDuration(parseFloat(sla.value))}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Steps List */}
          <div className="space-y-4">
            {workflowData?.steps?.map((step) => {
              const stepWeight = weights[step.step_id] || 0;
              const percentage = totalWeight > 0 ? (stepWeight / totalWeight) * 100 : 0;

              return (
                <div key={step.step_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{step.name}</div>
                      <div className="text-sm text-gray-600">{step.role_name} • Step {step.order}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium text-gray-900">{(stepWeight * 100).toFixed(0)}%</div>
                      <div className="text-sm text-gray-600">{percentage.toFixed(1)}% of total</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 mb-3">
                    <input
                      type="range"
                      min="0.1"
                      max="1"
                      step="0.01"
                      value={stepWeight}
                      onChange={(e) => handleWeightChange(step.step_id, parseFloat(e.target.value))}
                      className="flex-1"
                    />
                    <input
                      type="number"
                      min="0.1"
                      max="1"
                      step="0.01"
                      value={stepWeight}
                      onChange={(e) => handleWeightChange(step.step_id, parseFloat(e.target.value) || 0.1)}
                      className="w-16 px-2 py-1 border border-gray-300 rounded text-gray-900 text-center text-sm"
                    />
                  </div>

                  {/* SLA Breakdown for this step */}
                  <div className="grid grid-cols-4 gap-2 text-xs">
                    {[
                      { label: 'Urgent', value: workflowData?.slas?.urgent_sla },
                      { label: 'High', value: workflowData?.slas?.high_sla },
                      { label: 'Medium', value: workflowData?.slas?.medium_sla },
                      { label: 'Low', value: workflowData?.slas?.low_sla },
                    ].map((sla) => (
                      <div key={sla.label} className="text-center">
                        <div className="text-gray-500">{sla.label}</div>
                        <div className="text-gray-900">{calculateStepSLA(step.step_id, sla.value)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-between items-center">
          <div className="text-sm text-gray-600">
            {workflowData?.steps?.length || 0} steps
            {saveStatus === 'success' && (
              <span className="ml-2 text-green-600">✓ Saved successfully</span>
            )}
            {saveStatus === 'error' && (
              <span className="ml-2 text-red-600">✕ Error saving</span>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveWeights}
              disabled={isSaving}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save Weights'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
