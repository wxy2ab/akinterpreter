import React, { useState } from 'react';
import dynamic from 'next/dynamic';

const JsonEditor = dynamic(() => import('./JsonEditor'), { ssr: false });
const CodeEditor = dynamic(() => import('./CodeEditor'), { ssr: false });

interface MainWindowProps {
  currentPlan: any;
  stepCodes: { [key: string]: string };
  onPlanUpdate: (newPlan: any) => void;
  onCodeUpdate: (step: string, newCode: string) => void;
}

const MainWindow: React.FC<MainWindowProps> = ({
  currentPlan,
  stepCodes,
  onPlanUpdate,
  onCodeUpdate,
}) => {
  const [activeTab, setActiveTab] = useState('plan');

  const handlePlanChange = (newPlan: any) => {
    onPlanUpdate(newPlan);
  };

  const handleCodeChange = (step: string, newCode: string) => {
    onCodeUpdate(step, newCode);
  };

  const tabStyle = {
    padding: '10px 15px',
    cursor: 'pointer',
    backgroundColor: '#2d3748',
    color: '#a0aec0',
    border: 'none',
    borderRadius: '5px 5px 0 0',
    marginRight: '5px',
  };

  const activeTabStyle = {
    ...tabStyle,
    backgroundColor: '#4299e1',
    color: 'white',
  };

  const contentStyle = {
    height: 'calc(100% - 50px)',
    overflowY: 'auto' as const,
    padding: '20px',
    backgroundColor: '#1a202c',
    color: 'white',
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' as const, backgroundColor: '#2d3748' }}>
      <div style={{ display: 'flex', borderBottom: '1px solid #4a5568', padding: '10px' }}>
        <button
          style={activeTab === 'plan' ? activeTabStyle : tabStyle}
          onClick={() => setActiveTab('plan')}
        >
          Plan
        </button>
        {Object.keys(stepCodes).map((step, index) => (
          <button
            key={step}
            style={activeTab === step ? activeTabStyle : tabStyle}
            onClick={() => setActiveTab(step)}
          >
            Step {index + 1}
          </button>
        ))}
      </div>
      <div style={contentStyle}>
        {activeTab === 'plan' ? (
          <JsonEditor initialJson={currentPlan} onJsonChange={handlePlanChange} />
        ) : (
          <CodeEditor
            value={stepCodes[activeTab]}
            onChange={(newCode) => handleCodeChange(activeTab, newCode)}
            language="python"
          />
        )}
      </div>
    </div>
  );
};

export default MainWindow;