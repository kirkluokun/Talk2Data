import React from 'react';
import Sidebar from './Sidebar';
import ChatInterface from '../chat/ChatInterface';

const Layout: React.FC = () => {
  return (
    <div className="chat-container h-full">
      <Sidebar />
      <ChatInterface />
    </div>
  );
};

export default Layout; 