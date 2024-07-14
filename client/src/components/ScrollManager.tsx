'use client';

import React, { useEffect } from 'react';

const ScrollManager: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useEffect(() => {
    // 允许内部滚动，但防止整个页面滚动
    document.body.style.overflow = 'hidden';
    document.body.style.height = '100vh';
    document.body.style.width = '100vw';

    return () => {
      // Clean up
      document.body.style.overflow = '';
      document.body.style.height = '';
      document.body.style.width = '';
    };
  }, []);

  return <div className="h-full overflow-auto">{children}</div>;
};

export default ScrollManager;