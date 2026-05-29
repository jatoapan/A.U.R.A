import React from 'react';

function ScoreBar({ score }) {
  const maxScore = 100;
  const percentage = (score / maxScore) * 100;

  let bgColor = 'bg-green-500';
  if (score > 40 && score <= 75) {
    bgColor = 'bg-yellow-500';
  } else if (score > 75) {
    bgColor = 'bg-red-500';
  }

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full ${bgColor} transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="font-bold text-lg min-w-12 text-right">{score}/100</span>
    </div>
  );
}

export default ScoreBar;
