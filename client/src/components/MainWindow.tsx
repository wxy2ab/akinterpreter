'use client';

import React from 'react';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import CodeEditor from './CodeEditor';

interface MainWindowProps {
    currentPlan: any;
    stepCodes: { [key: string]: string };
}

const MainWindow: React.FC<MainWindowProps> = ({ currentPlan, stepCodes }) => {
    const hasPlanOrSteps = Object.keys(currentPlan).length > 0 || Object.keys(stepCodes).length > 0;

    return (
        <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            {!hasPlanOrSteps ? (
                <p>还没有生成计划</p>
            ) : (
                <Tabs style={{ width: '100%' }}>
                    <TabList>
                        {Object.keys(currentPlan).length > 0 && <Tab>Plan</Tab>}
                        {Object.keys(stepCodes).map((key, index) => (
                            <Tab key={key}>代码{index + 1}</Tab>
                        ))}
                    </TabList>

                    {Object.keys(currentPlan).length > 0 && (
                        <TabPanel>
                            <pre>{JSON.stringify(currentPlan, null, 2)}</pre>
                        </TabPanel>
                    )}
                    {Object.keys(stepCodes).map((key) => (
                        <TabPanel key={key}>
                            <CodeEditor value={stepCodes[key]} onChange={() => {}} />
                        </TabPanel>
                    ))}
                </Tabs>
            )}
        </div>
    );
};

export default MainWindow;
