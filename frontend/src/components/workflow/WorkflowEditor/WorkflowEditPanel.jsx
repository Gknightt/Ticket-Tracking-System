import React, { useState, useEffect } from 'react';
import { useWorkflowAPI } from '../../../api/useWorkflowAPI';

export default function WorkflowEditPanel({ workflow, onSave, readOnly = false }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    sub_category: '',
    department: '',
    end_logic: '',
    low_sla: '',
    medium_sla: '',
    high_sla: '',
    urgent_sla: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(!readOnly);

  const { updateWorkflowDetails } = useWorkflowAPI();

  useEffect(() => {
    if (workflow) {
      setFormData({
        name: workflow.name || '',
        description: workflow.description || '',
        category: workflow.category || '',
        sub_category: workflow.sub_category || '',
        department: workflow.department || '',
        end_logic: workflow.end_logic || '',
        low_sla: workflow.low_sla || '',
        medium_sla: workflow.medium_sla || '',
        high_sla: workflow.high_sla || '',
        urgent_sla: workflow.urgent_sla || '',
      });
      setIsEditing(!readOnly);
    }
  }, [workflow, readOnly]);

  const handleChange = (e) => {
    if (!isEditing) return;
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const updateData = {
        name: formData.name,
        description: formData.description,
        category: formData.category,
        sub_category: formData.sub_category,
        department: formData.department,
        end_logic: formData.end_logic,
        low_sla: formData.low_sla ? parseInt(formData.low_sla) : null,
        medium_sla: formData.medium_sla ? parseInt(formData.medium_sla) : null,
        high_sla: formData.high_sla ? parseInt(formData.high_sla) : null,
        urgent_sla: formData.urgent_sla ? parseInt(formData.urgent_sla) : null,
      };

      await updateWorkflowDetails(workflow.workflow_id, updateData);
      if (onSave) {
        onSave({
          ...workflow,
          ...updateData,
        });
      }
      setIsEditing(false);
    } catch (err) {
      setError(err.message || 'Failed to update workflow');
      console.error('Error updating workflow:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!workflow) {
    return (
      <div className="text-center text-gray-500 py-8">
        <p>Click on the canvas to view workflow properties</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-gray-700 mb-1">Workflow Name</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 disabled:bg-gray-100 disabled:text-gray-500"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-700 mb-1">Description</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            disabled={!isEditing}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 disabled:bg-gray-100 disabled:text-gray-500"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-700 mb-1">Category</label>
            <input
              type="text"
              name="category"
              value={formData.category}
              onChange={handleChange}
              disabled={!isEditing}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 disabled:bg-gray-100 disabled:text-gray-500"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-700 mb-1">Sub-Category</label>
            <input
              type="text"
              name="sub_category"
              value={formData.sub_category}
              onChange={handleChange}
              disabled={!isEditing}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 disabled:bg-gray-100 disabled:text-gray-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm text-gray-700 mb-1">Department</label>
          <input
            type="text"
            name="department"
            value={formData.department}
            onChange={handleChange}
            disabled={!isEditing}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 disabled:bg-gray-100 disabled:text-gray-500"
          />
        </div>

        {/* SLA Section */}
        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-900 mb-3">SLA Settings (seconds)</h4>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Urgent SLA</label>
              <input
                type="number"
                name="urgent_sla"
                value={formData.urgent_sla}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 text-sm disabled:bg-gray-100 disabled:text-gray-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">High SLA</label>
              <input
                type="number"
                name="high_sla"
                value={formData.high_sla}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 text-sm disabled:bg-gray-100 disabled:text-gray-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Medium SLA</label>
              <input
                type="number"
                name="medium_sla"
                value={formData.medium_sla}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 text-sm disabled:bg-gray-100 disabled:text-gray-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Low SLA</label>
              <input
                type="number"
                name="low_sla"
                value={formData.low_sla}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 text-sm disabled:bg-gray-100 disabled:text-gray-500"
              />
            </div>
          </div>
        </div>

        {!readOnly && (
          <div className="pt-4 flex gap-2">
            {!isEditing ? (
              <button
                type="button"
                onClick={() => setIsEditing(true)}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Edit
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={() => {
                    setIsEditing(false);
                    // Reset form data
                    if (workflow) {
                      setFormData({
                        name: workflow.name || '',
                        description: workflow.description || '',
                        category: workflow.category || '',
                        sub_category: workflow.sub_category || '',
                        department: workflow.department || '',
                        end_logic: workflow.end_logic || '',
                        low_sla: workflow.low_sla || '',
                        medium_sla: workflow.medium_sla || '',
                        high_sla: workflow.high_sla || '',
                        urgent_sla: workflow.urgent_sla || '',
                      });
                    }
                  }}
                  className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? 'Saving...' : 'Save'}
                </button>
              </>
            )}
          </div>
        )}
      </form>
    </div>
  );
}
