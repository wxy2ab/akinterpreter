import React, { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const newHeight = Math.min(textareaRef.current.scrollHeight, 5 * 24); // 假设每行高度为 24px
      textareaRef.current.style.height = `${newHeight}px`;
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end w-full">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        className="flex-grow p-2 bg-gray-800 text-white border border-gray-700 rounded-l-md resize-none"
        placeholder="输入消息... (Shift+Enter 换行)"
        disabled={disabled}
        rows={1}
        style={{
          minHeight: '38px',
          maxHeight: '120px', // 5行的大约高度
        }}
      />
      <button
        type="submit"
        className="p-2 bg-blue-600 text-white rounded-r-md h-full"
        disabled={disabled}
      >
        发送
      </button>
    </form>
  );
};

export default ChatInput;