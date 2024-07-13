import React from 'react';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/hljs';

interface MessageProps {
  type: string;
  content: any;
  isBot: boolean;
}

const ChatMessage: React.FC<MessageProps> = ({ type, content, isBot }) => {
  const renderContent = () => {
    if (typeof content === 'object') {
      return (
        <SyntaxHighlighter language="json" style={dracula}>
          {JSON.stringify(content, null, 2)}
        </SyntaxHighlighter>
      );
    }

    if (typeof content === 'string') {
      const cleanContent = content.replace(/^```(json|python)?\s*|\s*```$/g, '');

      // 尝试解析 JSON
      try {
        const jsonContent = JSON.parse(cleanContent);
        return (
          <SyntaxHighlighter language="json" style={dracula}>
            {JSON.stringify(jsonContent, null, 2)}
          </SyntaxHighlighter>
        );
      } catch (e) {
        // 如果不是 JSON，继续处理
      }

      // 检查是否是 Python 代码
      if (cleanContent.includes('def ') || cleanContent.includes('import ') || cleanContent.includes('print(')) {
        return (
          <SyntaxHighlighter language="python" style={dracula}>
            {cleanContent}
          </SyntaxHighlighter>
        );
      }

      // 处理图片和链接
      const parts = cleanContent.split(/(\!\[.*?\]\(.*?\)|\[.*?\]\(.*?\))/);
      return parts.map((part: string, index: number) => {
        if (part.startsWith('![')) {
          // 图片
          const match = part.match(/\!\[(.*?)\]\((.*?)\)/);
          if (match) {
            return (
              <img
                key={index}
                src={match[2]}
                alt={match[1]}
                className="max-w-full h-auto my-2"
                style={{ maxWidth: '100%', height: 'auto' }}
              />
            );
          }
        } else if (part.startsWith('[')) {
          // 链接
          const match = part.match(/\[(.*?)\]\((.*?)\)/);
          if (match) {
            return (
              <a key={index} href={match[2]} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                {match[1]}
              </a>
            );
          }
        }
        return <span key={index}>{part}</span>;
      });
    }

    return <p className="break-words whitespace-pre-wrap">{String(content)}</p>;
  };

  return (
    <div className={`max-w-3/4 ${isBot ? 'ml-0 mr-auto' : 'ml-auto mr-0'}`}>
      <div className={`p-3 rounded-lg ${isBot ? 'bg-gray-700 text-white' : 'bg-blue-500 text-white'} max-h-[80vh] overflow-y-auto`}>
        {renderContent()}
      </div>
    </div>
  );
};

export default ChatMessage;
