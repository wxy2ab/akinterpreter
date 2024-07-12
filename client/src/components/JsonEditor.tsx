// src/components/JsonEditor.tsx
import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { locale } from 'react-json-editor-ajrm/locale/en';

const JSONInput = dynamic(() => import('react-json-editor-ajrm'), { ssr: false });

interface JsonEditorProps {
    initialJson: any;
    onJsonChange: (updatedJson: any) => void;
}

const JsonEditorComponent: React.FC<JsonEditorProps> = ({ initialJson, onJsonChange }) => {
    const [json, setJson] = useState(initialJson);

    useEffect(() => {
        setJson(initialJson);
    }, [initialJson]);

    const handleJsonChange = (edit: any) => {
        const updatedJson = edit.json;
        setJson(updatedJson);
        onJsonChange(updatedJson);
    };

    return (
        <div style={{ height: '100%', width: '100%' }}>
            <JSONInput
                id="json-editor"
                placeholder={json}
                onChange={handleJsonChange}
                locale={locale}
                height="100%"
                width="100%"
                style={{ padding: '10px', borderRadius: '5px', boxShadow: '0 0 10px rgba(0, 0, 0, 0.1)' }}
            />
        </div>
    );
};

export default JsonEditorComponent;
