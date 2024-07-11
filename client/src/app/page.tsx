import React from 'react';
import ChatWindow from '@/components/ChatWindow';

const Home: React.FC = () => {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* 其他组件 */}
      <div className="flex-shrink-0">
        <h1 className="text-2xl font-bold p-4">来吧，来玩耍啊</h1>
        {/* 其他固定高度的组件 */}
      </div>
      
      {/* ChatWindow 将填充剩余空间 */}
      <div className="flex-grow overflow-hidden">
        <ChatWindow />
      </div>
    </div>
  );
};

export default Home;