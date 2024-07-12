import React, { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

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
    <form onSubmit={handleSubmit} className="flex items-end" style={{ backgroundColor: '#282a36' }}>
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        className="flex-grow p-2 border-none rounded-l resize-none overflow-hidden"
        placeholder="Type your message..."
        disabled={disabled}
        rows={1}
        style={{
          maxHeight: '150px',
          backgroundColor: '#44475a',
          color: '#f8f8f2',
          border: '1px solid #6272a4',
        }}
      />
      <button
        type="submit"
        className="p-2 text-white rounded-r h-full"
        disabled={disabled}
        style={{
          backgroundColor: '#6272a4',
          border: '1px solid #6272a4',
          cursor: disabled ? 'not-allowed' : 'pointer',
        }}
      >
        Send
      </button>
    </form>
  );
};

export default ChatInput;
