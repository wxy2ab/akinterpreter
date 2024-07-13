'use client';

import React, { useEffect } from 'react';

const ScrollManager: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useEffect(() => {
    const preventDefault = (e: Event) => e.preventDefault();

    // Disable scrolling on the window
    document.body.style.overflow = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.height = '100%';
    document.body.style.width = '100%';

    // Prevent default touch move behavior
    document.addEventListener('touchmove', preventDefault, { passive: false });

    return () => {
      // Clean up
      document.body.style.overflow = '';
      document.body.style.position = '';
      document.body.style.height = '';
      document.body.style.width = '';
      document.removeEventListener('touchmove', preventDefault);
    };
  }, []);

  return <>{children}</>;
};

export default ScrollManager;