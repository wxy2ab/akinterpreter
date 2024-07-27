import React, { useEffect, useRef } from 'react';
import Image from 'next/image';
import SyntaxHighlighter from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/hljs';

interface MessageProps {
  type: string;
  content: any;
  isBot: boolean;
  isLatest: boolean; // New prop to indicate if this is the latest message
  onContentRendered: () => void; // New callback prop
}

const ChatMessage: React.FC<MessageProps> = ({ type, content, isBot, isLatest, onContentRendered }) => {
  const messageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isLatest && messageRef.current) {
      onContentRendered();
    }
  }, [content, isLatest, onContentRendered]);
  const renderContent = () => {
    if (typeof content === 'object') {
      return (
        <SyntaxHighlighter language="json" style={dracula}>
          {JSON.stringify(content, null, 2)}
        </SyntaxHighlighter>
      );
    }

    if (typeof content === 'string') {
      const codeBlockRegex = /^```(json|python)?\s*([\s\S]*?)```$/;
      const match = content.match(codeBlockRegex);

      if (match) {
        const language = match[1] || 'text';
        const code = match[2].trim();

        if (language === 'json') {
          try {
            const jsonContent = JSON.parse(code);
            return (
              <SyntaxHighlighter language="json" style={dracula}>
                {JSON.stringify(jsonContent, null, 2)}
              </SyntaxHighlighter>
            );
          } catch (e) {
            // If JSON parsing fails, treat it as regular code
          }
        }

        return (
          <SyntaxHighlighter language={language} style={dracula}>
            {code}
          </SyntaxHighlighter>
        );
      }

      // Check if it's Python code
      if (content.includes('def ') || content.includes('import ') || content.includes('print(')) {
        return (
          <SyntaxHighlighter language="python" style={dracula}>
            {content}
          </SyntaxHighlighter>
        );
      }

      // Handle images and links
      const parts = content.split(/(\!\[.*?\]\(.*?\)|\[.*?\]\(.*?\))/);
      return parts.map((part: string, index: number) => {
        if (part.startsWith('![')) {
          // Image
          const imageMatch = part.match(/\!\[(.*?)\]\((.*?)\)/);
          if (imageMatch) {
            return (
              <div key={index} className="relative w-full h-64 my-2">
                <Image
                  src={imageMatch[2]}
                  alt={imageMatch[1]}
                  layout="fill"
                  objectFit="contain"
                />
              </div>
            );
          }
        } else if (part.startsWith('[')) {
          // Link
          const linkMatch = part.match(/\[(.*?)\]\((.*?)\)/);
          if (linkMatch) {
            return (
              <a key={index} href={linkMatch[2]} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                {linkMatch[1]}
              </a>
            );
          }
        }
        // Regular text
        return <span key={index} className="whitespace-pre-wrap">{part}</span>;
      });
    }

    return <p className="break-words whitespace-pre-wrap">{String(content)}</p>;
  };

  return (
    <div 
      ref={messageRef}
      className={`max-w-3/4 ${isBot ? 'ml-0 mr-auto' : 'ml-auto mr-0'}`}
    >
      <div className={`p-3 rounded-lg ${isBot ? 'bg-gray-700 text-white' : 'bg-blue-500 text-white'} max-h-[80vh] overflow-y-auto`}>
        {renderContent()}
      </div>
    </div>
  );
};

export default ChatMessage;