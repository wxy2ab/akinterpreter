// src/components/CodeEditor.tsx
import React from 'react';
import { Controlled as CodeMirror } from 'react-codemirror2';
import 'codemirror/lib/codemirror.css';
import 'codemirror/theme/material.css';
import 'codemirror/mode/python/python';

interface CodeEditorProps {
    value: string;
    onChange: (value: string) => void;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ value, onChange }) => {
    return (
        <CodeMirror
            value={value}
            options={{
                mode: 'python',
                theme: 'material',
                lineNumbers: true,
                readOnly: true,
            }}
            onBeforeChange={(editor, data, value) => {
                onChange(value);
            }}
        />
    );
};

export default CodeEditor;
