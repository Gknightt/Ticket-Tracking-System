import React, { useCallback } from 'react';
import { Handle, Position } from 'reactflow';
import { Circle, Flag } from 'lucide-react';

export default function StepNode({ data, selected }) {

  const handleNodeClick = useCallback(() => {
    if (data.onStepClick) {
      data.onStepClick(data);
    }
  }, [data]);

  return (
    <div
      className={`px-4 py-3 rounded-lg bg-white border-2 shadow-sm transition-all min-w-[180px] cursor-pointer ${
        selected
          ? 'border-blue-500 shadow-md'
          : 'border-gray-300 hover:border-gray-400'
      } ${data.is_start ? 'border-l-4 border-l-green-500' : ''} ${data.is_end ? 'border-l-4 border-l-red-500' : ''}`}
      onClick={handleNodeClick}
    >
      {!data.is_start && (
        <>
          <Handle type="target" position={Position.Top} id="top" className="w-3 h-3 bg-blue-500" />
          <Handle type="target" position={Position.Left} id="left" className="w-3 h-3 bg-blue-500" />
          <Handle type="target" position={Position.Right} id="right" className="w-3 h-3 bg-blue-500" />
        </>
      )}
      
      <div className="flex items-start gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="text-gray-900 font-medium">{data.label}</span>
            {data.is_start && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-green-100 text-green-700 text-xs">
                <Circle className="w-3 h-3" />
                START
              </span>
            )}
            {data.is_end && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs">
                <Flag className="w-3 h-3" />
                END
              </span>
            )}
          </div>
          {data.role && (
            <div className="text-sm text-gray-600">{data.role}</div>
          )}
          {data.description && (
            <div className="text-xs text-gray-500 mt-1 line-clamp-2">{data.description}</div>
          )}
        </div>
      </div>

      {!data.is_end && (
        <>
          <Handle type="source" position={Position.Bottom} id="bottom" className="w-3 h-3 bg-blue-500" />
          <Handle type="source" position={Position.Left} id="left" className="w-3 h-3 bg-blue-500" />
          <Handle type="source" position={Position.Right} id="right" className="w-3 h-3 bg-blue-500" />
        </>
      )}
    </div>
  );
}
