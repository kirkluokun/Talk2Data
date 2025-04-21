import React from 'react';
import useChat from '../../hooks/useChat';

/**
 * 侧边栏组件，显示对话历史列表和新建对话按钮
 */
const Sidebar: React.FC = () => {
  // 使用 useChat hook 获取对话相关状态和方法
  const {
    conversations,
    selectedConversationId,
    isLoadingHistory,
    error,
    fetchHistory,
    selectConversation,
    createNewConversation,
    deleteConversation,
  } = useChat();

  // 组件挂载时加载对话历史
  React.useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // 删除对话确认
  const handleDeleteConversation = (e: React.MouseEvent, id: number) => {
    e.stopPropagation(); // 阻止事件冒泡，避免触发选择对话
    if (window.confirm('确定要删除此对话吗？')) {
      deleteConversation(id);
    }
  };

  return (
    <div className="sidebar">
      {/* 移除顶部的标题和新建按钮区域 */}
      {/* 
      <div className="p-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
        <h2 className="font-semibold">Talk2FinancialData</h2>
        <button 
          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          onClick={createNewConversation}
          aria-label="新建对话"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
        </button>
      </div>
      */}
      
      <div className="p-4 flex-1 overflow-y-auto">
        <div className="text-sm text-gray-500 mb-2">历史对话</div>
        
        {error && (
          <div className="p-2 text-sm text-red-500 bg-red-50 dark:bg-red-900/20 rounded mb-2">
            {error}
          </div>
        )}
        
        {isLoadingHistory ? (
          // 加载状态显示
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="p-2 rounded bg-gray-100 dark:bg-gray-800 animate-pulse h-10"></div>
            ))}
          </div>
        ) : conversations.length > 0 ? (
          // 对话列表
          <div className="space-y-2">
            {conversations.map((conversation) => (
              <div 
                key={conversation.id}
                className={`p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700 cursor-pointer flex justify-between items-center ${
                  selectedConversationId === conversation.id ? 'bg-gray-200 dark:bg-gray-700' : ''
                }`}
                onClick={() => selectConversation(conversation.id)}
              >
                <div className="truncate flex-1">
                  {conversation.title}
                </div>
                <button
                  className="text-gray-400 hover:text-red-500 dark:hover:text-red-400 ml-2 p-1"
                  onClick={(e) => handleDeleteConversation(e, conversation.id)}
                  aria-label="删除对话"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        ) : (
          // 无对话时显示
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            没有历史对话
          </div>
        )}
      </div>
      
      <div className="p-4 border-t border-gray-200 dark:border-gray-800">
        <button 
          className="w-full py-2 px-4 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 flex items-center justify-center"
          onClick={createNewConversation}
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5 mr-2">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          新建对话
        </button>
      </div>
    </div>
  );
};

export default Sidebar; 