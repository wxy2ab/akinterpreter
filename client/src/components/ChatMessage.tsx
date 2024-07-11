import React from 'react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { docco } from 'react-syntax-highlighter/dist/esm/styles/hljs';

interface MessageProps {
  type: string;
  content: any;
  isBot: boolean;
}

const ChatMessage: React.FC<MessageProps> = ({ type, content, isBot }) => {
  const renderCodeBlock = (code: string, language: string) => {
    return (
      <div className="max-h-96 overflow-y-auto my-2">
        <SyntaxHighlighter language={language} style={docco}>
          {code}
        </SyntaxHighlighter>
      </div>
    );
  };

  const renderJsonContent = (jsonString: string) => {
    try {
      const jsonContent = JSON.parse(jsonString);
      return renderCodeBlock(JSON.stringify(jsonContent, null, 2), 'json');
    } catch (e) {
      console.error("Error parsing JSON:", e);
      return <p className="break-words whitespace-pre-wrap">{jsonString}</p>;
    }
  };

  const renderContent = () => {
    if (typeof content === 'string') {
      // 使用正则表达式匹配 ```json ... ``` 和 ```python ... ``` 块
      const parts = content.split(/(```(json|python)\s*[\s\S]*?```)/);
      return parts.map((part, index) => {
        if (part.startsWith('```json')) {
          const jsonContent = part.replace(/```json\s*/, '').replace(/\s*```$/, '');
          return <React.Fragment key={index}>{renderJsonContent(jsonContent)}</React.Fragment>;
        } else if (part.startsWith('```python')) {
          const pythonCode = part.replace(/```python\s*/, '').replace(/\s*```$/, '');
          return <React.Fragment key={index}>{renderCodeBlock(pythonCode, 'python')}</React.Fragment>;
        } else {
          return <p key={index} className="break-words whitespace-pre-wrap">{part}</p>;
        }
      });
    } else if (typeof content === 'object') {
      return renderJsonContent(JSON.stringify(content));
    } else {
      return <p className="break-words whitespace-pre-wrap">{String(content)}</p>;
    }
  };

  return (
    <div className={`max-w-3/4 ${isBot ? 'ml-0 mr-auto' : 'ml-auto mr-0'}`}>
      <div className={`p-3 rounded-lg ${isBot ? 'bg-gray-200' : 'bg-blue-500 text-white'} max-h-[80vh] overflow-y-auto`}>
        {renderContent()}
      </div>
    </div>
  );
};

export default ChatMessage;