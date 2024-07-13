'use client';

import React from 'react';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import JsonCodeEditor from './JsonCodeEditor';
import CodeEditor from './CodeEditor';

interface MainWindowProps {
  currentPlan: any;
  stepCodes: { [key: string]: string };
}

const MainWindow: React.FC<MainWindowProps> = ({ currentPlan = {}, stepCodes = {} }) => {
  const hasPlanOrSteps = Object.keys(currentPlan).length > 0 || Object.keys(stepCodes).length > 0;

  return (
    <div style={{ height: '100%', width: '100%', display: 'flex', flexDirection: 'column' }}>
      {!hasPlanOrSteps ? (
        <p>还没有生成计划</p>
      ) : (
        <Tabs style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <TabList style={{ flexShrink: 0 }}>
            {Object.keys(currentPlan).length > 0 && <Tab>Plan</Tab>}
            {Object.keys(stepCodes).map((key, index) => (
              <Tab key={key}>代码{index + 1}</Tab>
            ))}
          </TabList>

          <div style={{ flex: 1, overflow: 'auto' }}>
            {Object.keys(currentPlan).length > 0 && (
              <TabPanel style={{ height: '100%' }}>
                <JsonCodeEditor value={currentPlan} onChange={() => {}} />
              </TabPanel>
            )}
            {Object.keys(stepCodes).map((key) => (
              <TabPanel key={key} style={{ height: '100%' }}>
                <CodeEditor value={stepCodes[key]} onChange={() => {}} />
              </TabPanel>
            ))}
          </div>
        </Tabs>
      )}
    </div>
  );
};

export default MainWindow;
