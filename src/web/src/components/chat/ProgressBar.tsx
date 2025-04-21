import React from 'react';

type ProgressBarProps = {
  progress: number;
  stage?: string;
};

// ProgressBar组件：显示进度条
const ProgressBar: React.FC<ProgressBarProps> = ({ progress, stage }) => {
  // 确保进度在0-100范围内
  const normalizedProgress = Math.min(Math.max(0, progress), 100);
  
  return (
    <div className="progress-container">
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
        <div 
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
          style={{ width: `${normalizedProgress}%` }}
        ></div>
      </div>
      <div className="text-xs text-gray-500 flex justify-between">
        <div>{stage || '处理中...'}</div>
        <div className="font-medium">{Math.round(normalizedProgress)}%</div>
      </div>
    </div>
  );
};

export default ProgressBar; 