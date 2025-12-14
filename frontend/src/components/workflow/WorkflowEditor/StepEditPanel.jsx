import React, { useState, useEffect } from 'react';
import { Trash2 } from 'lucide-react';

export default function StepEditPanel({ step, roles = [], onUpdate, onDelete }) {
  const [formData, setFormData] = useState({
    label: '',
    role: '',
    description: '',
    instruction: '',
    is_start: false,
    is_end: false,
  });

  useEffect(() => {
    if (step) {
      setFormData({
        label: step.label || step.name || '',
        role: step.role || '',
        description: step.description || '',
        instruction: step.instruction || '',
        is_start: step.is_start || step.isStart || false,
        is_end: step.is_end || step.isEnd || false,
      });
    }
  }, [step]);

  const handleChange = (field, value) => {
    const newFormData = { ...formData, [field]: value };
    setFormData(newFormData);
    if (onUpdate) {
      onUpdate({
        name: newFormData.label,
        label: newFormData.label,
        role: newFormData.role,
        description: newFormData.description,
        instruction: newFormData.instruction,
        is_start: newFormData.is_start,
        is_end: newFormData.is_end,
      });
    }
  };

  if (!step) return null;

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm text-gray-700 mb-1">Step Name</label>
        <input
          type="text"
          value={formData.label}
          onChange={(e) => handleChange('label', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-700 mb-1">Assigned Role</label>
        {roles.length > 0 ? (
          <select
            value={formData.role}
            onChange={(e) => handleChange('role', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select a role</option>
            {roles.map((role) => (
              <option key={role.role_id || role.id} value={role.name}>
                {role.name}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            value={formData.role}
            onChange={(e) => handleChange('role', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="e.g., Admin, Manager, Customer"
          />
        )}
      </div>

      <div>
        <label className="block text-sm text-gray-700 mb-1">Description</label>
        <textarea
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter step description"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-700 mb-1">Instruction</label>
        <textarea
          value={formData.instruction}
          onChange={(e) => handleChange('instruction', e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="Enter step instruction"
        />
      </div>

      <div className="pt-4 border-t border-gray-200 space-y-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={formData.is_start}
            onChange={(e) => handleChange('is_start', e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Mark as START step</span>
        </label>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={formData.is_end}
            onChange={(e) => handleChange('is_end', e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Mark as END step</span>
        </label>
      </div>

      {onDelete && !formData.is_start && !formData.is_end && (
        <div className="pt-4 border-t border-gray-200">
          <button
            onClick={onDelete}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete Step
          </button>
        </div>
      )}
    </div>
  );
}
