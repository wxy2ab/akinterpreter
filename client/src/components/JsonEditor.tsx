import React, { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';

interface JsonEditorProps {
  initialJson: any;
  onJsonChange: (updatedJson: any) => void;
}

const JsonEditor: React.FC<JsonEditorProps> = ({ initialJson, onJsonChange }) => {
  const [value, setValue] = useState<string>(JSON.stringify(initialJson, null, 2));

  useEffect(() => {
    setValue(JSON.stringify(initialJson, null, 2));
  }, [initialJson]);

  const handleEditorChange = (value: string | undefined) => {
    if (value === undefined) return;
    setValue(value);
    try {
      const parsedJson = JSON.parse(value);
      onJsonChange(parsedJson);
    } catch (error) {
      console.error('Invalid JSON detected:', error);
    }
  };

  return (
    <Editor
      height="100%"
      defaultLanguage="json"
      defaultValue={value}
      value={value}
      onChange={handleEditorChange}
      theme="vs-dark"
      options={{
        automaticLayout: true,
        wordWrap: 'on',
        formatOnType: true,
      }}
    />
  );
};

export default JsonEditor;
