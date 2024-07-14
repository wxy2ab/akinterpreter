import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { JSONInputProps } from 'react-json-editor-ajrm';
import locale from 'react-json-editor-ajrm/locale/en';


const JSONEditor = dynamic<JSONInputProps>(
  () => import('react-json-editor-ajrm').then((mod) => mod.default),
  { ssr: false }
);

interface JsonEditorProps {
  initialJson: any;
  onJsonChange: (updatedJson: any) => void;
}

const JsonEditor: React.FC<JsonEditorProps> = ({ initialJson, onJsonChange }) => {
  const [json, setJson] = useState(initialJson);

  useEffect(() => {
    setJson(initialJson);
  }, [initialJson]);

  const handleJsonChange = (data: { jsObject: any } | { error: boolean }) => {
    if ('jsObject' in data) {
      setJson(data.jsObject);
      onJsonChange(data.jsObject);
    }
  };

  return (
    <div style={{ height: '100%', width: '100%', fontSize: '16px'  }}>
      <JSONEditor
        id="json-editor"
        placeholder={json}
        onChange={handleJsonChange}
        locale={locale}
        height="100%"
        width="100%"
        colors={{
          background: '#1a202c',
          default: '#d4d4d4',
        }}
      />
    </div>
  );
};

export default JsonEditor;