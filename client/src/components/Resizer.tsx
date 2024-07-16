import React, { useState, useCallback, useEffect } from 'react';

interface ResizerProps {
  onResize: (newLeftWidth: number) => void;
}

const Resizer: React.FC<ResizerProps> = ({ onResize }) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleMouseDown = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging) return;

      const newLeftWidth = (e.clientX / window.innerWidth) * 100;
      onResize(Math.max(10, Math.min(90, newLeftWidth))); // Limit between 10% and 90%
    },
    [isDragging, onResize]
  );

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    } else {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div
      className="w-1 bg-gray-300 hover:bg-blue-500 cursor-col-resize"
      onMouseDown={handleMouseDown}
    />
  );
};

export default Resizer;