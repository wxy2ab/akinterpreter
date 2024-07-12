import React, { useEffect, useRef } from 'react';
import { useCodeMirror } from '@uiw/react-codemirror';
import { json, jsonLanguage } from '@codemirror/lang-json';
import { python } from '@codemirror/lang-python';
import { dracula } from '@uiw/codemirror-theme-dracula';
import { EditorView } from '@codemirror/view';

interface JsonCodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language: 'json' | 'python';
}

const JsonCodeEditor: React.FC<JsonCodeEditorProps> = ({ value, onChange, language }) => {
  const editorRef = useRef<HTMLDivElement>(null);

  const getExtensions = () => {
    const baseExtensions = [
      dracula,
      EditorView.theme({
        "&": {
          fontSize: "16px",
        },
        ".cm-content": {
          backgroundColor: "#282a36",
          color: "#f8f8f2",
        },
        ".cm-scroller": {
          backgroundColor: "#282a36",
        },
      }),
    ];

    if (language === 'json') {
      return [...baseExtensions, json()];
    } else if (language === 'python') {
      return [...baseExtensions, python()];
    }
    return baseExtensions;
  };

  const { setContainer, view } = useCodeMirror({
    container: editorRef.current,
    value,
    extensions: getExtensions(),
    onChange: (value) => onChange(value),
  });

  useEffect(() => {
    if (editorRef.current) {
      setContainer(editorRef.current);
    }
  }, [setContainer]);

  return <div ref={editorRef} style={{ height: '100%' }} />;
};

export default JsonCodeEditor;
