import React from 'react';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';
import Image from 'next/image';

// 注册语言
SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('json', json);

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
      return parts.map((part, index) => {
        if (part.startsWith('![')) {
          // 图片
          const match = part.match(/\!\[(.*?)\]\((.*?)\)/);
          if (match) {
            return (
              <div key={index} className="my-2">
                <Image src={match[2]} alt={match[1]} layout="responsive" width={600} height={400} />
              </div>
            );
          }
        } else if (part.startsWith('[')) {
          // 链接
          const match = part.match(/\[(.*?)\]\((.*?)\)/);
          if (match) {
            return <a key={index} href={match[2]} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">{match[1]}</a>;
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
