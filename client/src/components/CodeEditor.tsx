import React from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { dracula } from '@uiw/codemirror-theme-dracula';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ value, onChange }) => {
  return (
    <div style={{ height: '100%', overflowY: 'auto' }}>
      <CodeMirror
        value={value}
        height="100%"
        extensions={[python()]}
        theme={dracula}
        onChange={(value) => onChange(value)}
        basicSetup={{ lineNumbers: true }}
      />
    </div>
  );
};

export default CodeEditor;
