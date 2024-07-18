import React, { useState, useMemo } from 'react';
import JsonEditor from './JsonEditor';
import CodeEditor from './CodeEditor';

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
  const [error, setError] = useState<string | null>(null);

  const validateJson = (json: any): object | any[] => {
    if (typeof json === 'object' && json !== null) {
      return json;
    }
    try {
      const parsedJson = JSON.parse(json);
      if (typeof parsedJson === 'object' && parsedJson !== null) {
        return parsedJson;
      }
    } catch (error) {
      console.error('Invalid JSON string provided, using empty object as fallback.', error);
    }
    return {};
  };

  const validCurrentPlan = useMemo(() => {
    return validateJson(currentPlan);
  }, [currentPlan]);

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
        {error && <div className="error-message">{error}</div>}
        {activeTab === 'plan' ? (
          <JsonEditor 
            key={JSON.stringify(validCurrentPlan)}  // Force re-render on plan change
            initialJson={validCurrentPlan} 
            onJsonChange={(updatedJson) => {
              try {
                const validJson = validateJson(updatedJson);
                onPlanUpdate(validJson);
              } catch (error) {
                setError('Failed to update JSON. Please check the console for more details.');
              }
            }}  
          />
        ) : (
          <CodeEditor
            value={stepCodes[activeTab]}
            onChange={(newCode) => onCodeUpdate(activeTab, newCode)}
            language="python"
          />
        )}
      </div>
    </div>
  );
};

export default MainWindow;
