import React, { useEffect, useState } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { json } from '@codemirror/lang-json';
import '@uiw/react-codemirror/dist/codemirror.css';

interface JsonEditorProps {
  initialJson: any;
  onJsonChange: (updatedJson: any) => void;
}

const JsonEditor: React.FC<JsonEditorProps> = ({ initialJson, onJsonChange }) => {
  const [value, setValue] = useState<string>(JSON.stringify(initialJson, null, 2));

  useEffect(() => {
    setValue(JSON.stringify(initialJson, null, 2));
  }, [initialJson]);

  const handleChange = (value: string) => {
    setValue(value);
    try {
      const parsedJson = JSON.parse(value);
      onJsonChange(parsedJson);
    } catch (error) {
      console.error('Invalid JSON detected:', error);
    }
  };

  return (
    <CodeMirror
      value={value}
      extensions={[json()]}
      onChange={(value) => handleChange(value)}
      theme="dark"
      basicSetup={{ lineNumbers: true }}
    />
  );
};

export default JsonEditor;
