import React from 'react';

interface ToolbarProps {
  onExecutePlan: () => void;
  onClearHistory: () => void;
  onResetPlan: () => void;
}

const Toolbar: React.FC<ToolbarProps> = ({ onExecutePlan, onClearHistory, onResetPlan }) => {
  const buttonStyle: React.CSSProperties = {
    margin: '0 10px',
    padding: '5px 10px',
    backgroundColor: '#4a5568',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  };

  const toolbarStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    padding: '10px',
    backgroundColor: '#2d3748',
    color: 'white',
  };

  return (
    <div style={toolbarStyle}>
      <button style={buttonStyle} onClick={onExecutePlan}>执行计划</button>
      <button style={buttonStyle} onClick={onClearHistory}>清空聊天记录</button>
      <button style={buttonStyle} onClick={onResetPlan}>重置计划</button>
    </div>
  );
};

export default Toolbar;