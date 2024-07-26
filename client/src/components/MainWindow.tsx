import React, { useState, useMemo, useCallback, useRef } from 'react';
import JsonEditor from './JsonEditor';
import CodeEditor from './CodeEditor';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

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
  const updateTimeout = useRef<NodeJS.Timeout | null>(null);

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

  const handleJsonChange = (updatedJson: any) => {
    if (updateTimeout.current) {
      clearTimeout(updateTimeout.current);
    }

    updateTimeout.current = setTimeout(() => {
      try {
        const validJson = validateJson(updatedJson);
        onPlanUpdate(validJson);
      } catch (error) {
        setError('Failed to update JSON. Please check the console for more details.');
      }
    }, 2000); // 2秒后调用API
  };


  return (
    <div className="h-full flex flex-col bg-gray-800">
      <Tabs defaultValue="plan" className="w-full h-full flex flex-col">
        <TabsList className="flex justify-start border-b border-gray-700 bg-gray-800">
          <TabsTrigger value="plan" className="px-4 py-2">Plan</TabsTrigger>
          {Object.keys(stepCodes).map((step, index) => (
            <TabsTrigger key={step} value={step} className="px-4 py-2">
              Step {index + 1}
            </TabsTrigger>
          ))}
        </TabsList>
        {error && <div className="error-message text-red-500 p-2">{error}</div>}
        <div className="flex-grow overflow-hidden">
          <TabsContent value="plan" className="h-full">
            <div className="h-full p-4">
              <JsonEditor 
                key={JSON.stringify(validCurrentPlan)}
                initialJson={validCurrentPlan} 
                onJsonChange={handleJsonChange}  
              />
            </div>
          </TabsContent>
          {Object.entries(stepCodes).map(([step, code]) => (
            <TabsContent key={step} value={step} className="h-full">
              <div className="h-full p-4">
                <CodeEditor
                  value={code}
                  onChange={(newCode) => onCodeUpdate(step, newCode)}
                  language="python"
                />
              </div>
            </TabsContent>
          ))}
        </div>
      </Tabs>
    </div>
  );
};

export default MainWindow;
