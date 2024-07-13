import React from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { json } from '@codemirror/lang-json';
import { dracula } from '@uiw/codemirror-theme-dracula';

interface JsonCodeEditorProps {
  value: any;
  onChange: (value: any) => void;
}

const JsonCodeEditor: React.FC<JsonCodeEditorProps> = ({ value, onChange }) => {
  return (
    <div style={{ height: '100%', overflowY: 'auto' }}>
      <CodeMirror
        value={JSON.stringify(value, null, 2)}
        height="100%"
        extensions={[json()]}
        theme={dracula}
        onChange={(value) => onChange(JSON.parse(value))}
        basicSetup={{ lineNumbers: true }}
      />
    </div>
  );
};

export default JsonCodeEditor;
