'use client';

import React from 'react';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import JsonCodeEditor from './JsonCodeEditor';

interface MainWindowProps {
    currentPlan: any;
    stepCodes: { [key: string]: string };
}

const MainWindow: React.FC<MainWindowProps> = ({ currentPlan, stepCodes }) => {
    const hasPlanOrSteps = Object.keys(currentPlan).length > 0 || Object.keys(stepCodes).length > 0;

    return (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', backgroundColor: '#282a36', color: '#f8f8f2' }}>
            {!hasPlanOrSteps ? (
                <p>还没有生成计划</p>
            ) : (
                <Tabs style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
                    <TabList>
                        {Object.keys(currentPlan).length > 0 && <Tab>Plan</Tab>}
                        {Object.keys(stepCodes).map((key, index) => (
                            <Tab key={key}>代码{index + 1}</Tab>
                        ))}
                    </TabList>

                    {Object.keys(currentPlan).length > 0 && (
                        <TabPanel style={{ height: '100%', overflowY: 'auto' }}>
                            <JsonCodeEditor value={JSON.stringify(currentPlan, null, 2)} onChange={() => {}} language="json" />
                        </TabPanel>
                    )}
                    {Object.keys(stepCodes).map((key) => (
                        <TabPanel key={key} style={{ height: '100%', overflowY: 'auto' }}>
                            <JsonCodeEditor value={stepCodes[key]} onChange={() => {}} language="python" />
                        </TabPanel>
                    ))}
                </Tabs>
            )}
        </div>
    );
};

export default MainWindow;
