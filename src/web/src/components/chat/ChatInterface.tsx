import React, { useRef, useEffect, useState } from 'react';
import Message from './Message';
import ChatInput from './ChatInput';
import ProgressBar from './ProgressBar';
import useChat from '../../hooks/useChat';
import { MessageType } from '../../types/chat';

/**
 * 聊天界面组件
 * 使用useChat hook获取全局聊天状态并显示对话内容
 */
const ChatInterface: React.FC = () => {
  // 使用useChat hook获取聊天状态和方法
  const {
    messages,
    isLoadingMessages,
    isSendingMessage,
    currentJobProgress,
    error,
    sendMessage,
    clearError
  } = useChat();
  
  // 模拟消息状态，仅用于开发测试
  const [mockMessages, setMockMessages] = useState<MessageType[]>([]);
  // 模拟进度状态，仅用于开发测试
  const [mockProgress, setMockProgress] = useState({
    isActive: false,
    progress: 0,
    stage: ''
  });
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // --- 新增: 管理聊天输入框的状态 ---
  const [inputValue, setInputValue] = useState('');
  // --- 结束新增 ---

  // 当收到新消息时，滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, mockMessages]);

  // 清理模拟进度定时器
  useEffect(() => {
    let progressInterval: number | null = null;
    
    return () => {
      if (progressInterval) window.clearInterval(progressInterval);
    };
  }, []);

  // 测试用的模拟API调用函数，当真实API不可用时使用
  const mockApiCall = async (_query: string) => {
    return new Promise<{ job_id: string }>(resolve => {
      setTimeout(() => {
        resolve({ job_id: Date.now().toString() });
      }, 500);
    });
  };

  // 启动模拟进度条
  const startMockProgress = () => {
    let progress = 0;
    const stages = ['查询解析中...', '数据获取中...', '数据分析中...'];
    let currentStage = 0;
    
    setMockProgress({
      isActive: true,
      progress: 0,
      stage: stages[0]
    });
    
    const interval = window.setInterval(() => {
      progress += 5;
      
      if (progress >= 33 && progress < 66 && currentStage === 0) {
        currentStage = 1;
      } else if (progress >= 66 && currentStage === 1) {
        currentStage = 2;
      }
      
      setMockProgress({
        isActive: true,
        progress,
        stage: stages[Math.min(currentStage, 2)]
      });
      
      if (progress >= 100) {
        window.clearInterval(interval);
        
        setTimeout(() => {
          setMockProgress({
            isActive: false,
            progress: 0,
            stage: ''
          });
        }, 500);
      }
    }, 200);
    
    return interval;
  };

  /**
   * 处理发送消息
   * 首先尝试使用useChat提供的sendMessage方法
   * 如果失败且环境为开发环境，则回退到模拟API
   */
  const handleSendMessage = async (content: string) => {
    if (content.trim() === '') return;
    
    try {
      // 首先尝试使用useChat发送消息
      await sendMessage(content);
      // --- 新增: 发送成功后清空输入框 ---
      setInputValue(''); 
      // --- 结束新增 ---
      // 如果使用了useChat的sendMessage方法，清空模拟消息
      setMockMessages([]);
    } catch (error) {
      console.error('发送消息失败，尝试使用模拟响应:', error);
      
      // 开发环境下使用模拟API (仅用于开发测试)
      if (process.env.NODE_ENV === 'development') {
        try {
          // 创建临时用户消息
          const tempUserMessage: MessageType = {
            id: Date.now().toString(),
            content: content,
            isUser: true,
            timestamp: new Date().toLocaleTimeString()
          };
          
          // 添加用户消息到模拟消息列表
          setMockMessages(prev => [...prev, tempUserMessage]);
          
          // 启动模拟进度条
          const progressInterval = startMockProgress();
          
          // 模拟API调用延迟
          await mockApiCall(content);
          
          // 添加模拟AI回复
          setTimeout(() => {
            // 随机选择一种内容类型进行测试
            const mockTypes = ['text', 'dataframe_csv_path', 'plot_file_path'];
            const mockType = mockTypes[Math.floor(Math.random() * mockTypes.length)];
            
            let mockContent = `这是对 "${content}" 的模拟回答。实际开发中将显示真实的API响应。`;
            let mockFilePath = '';
            
            if (mockType === 'dataframe_csv_path') {
              mockContent = '数据表格已生成：';
              mockFilePath = 'samples/mock_data.csv'; // 假设有个示例CSV文件
            } else if (mockType === 'plot_file_path') {
              mockContent = '图表已生成：';
              mockFilePath = 'samples/mock_chart.png'; // 假设有个示例图片文件
            }
            
            const mockAiMessage: MessageType = {
              id: (Date.now() + 1).toString(),
              content: mockContent,
              isUser: false,
              timestamp: new Date().toLocaleTimeString(),
              contentType: mockType,
              filePath: mockFilePath
            };
            
            // 添加AI回复到模拟消息列表
            setMockMessages(prev => [...prev, mockAiMessage]);
            
            // 清除进度条
            window.clearInterval(progressInterval);
            setMockProgress({
              isActive: false,
              progress: 0,
              stage: ''
            });
          }, 2500);
          
        } catch (mockError) {
          console.error('模拟API调用也失败:', mockError);
          setMockProgress({
            isActive: false,
            progress: 0,
            stage: ''
          });
        }
      }
    }
  };

  // 合并全局消息和模拟消息
  const displayMessages = mockMessages.length > 0 ? mockMessages : messages;
  // 使用模拟进度条或全局进度条
  const displayProgress = mockProgress.isActive ? mockProgress : currentJobProgress;

  return (
    <div className="chat-content flex flex-col h-full">
      {/* 消息列表区域 */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* 显示加载消息状态 */}
        {isLoadingMessages && (
          <div className="flex justify-center my-4">
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-3 animate-pulse">
              加载对话历史...
            </div>
          </div>
        )}
        
        {/* 显示错误信息 */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 text-red-500 p-3 rounded-lg mb-4">
            {error}
            <button 
              onClick={clearError}
              className="ml-2 text-xs underline hover:no-underline"
            >
              清除
            </button>
          </div>
        )}
        
        {/* 空状态提示 */}
        {displayMessages.length === 0 && !isLoadingMessages && (
          <div className="flex flex-col items-center justify-center h-full text-gray-500 dark:text-gray-400">
            <div className="text-center p-4">
              <p className="mb-2 text-lg">欢迎使用 Talk2FinancialData</p>
              <p>您可以询问有关金融数据的问题，例如：</p>
              {/* 修改示例问题列表，并添加点击事件填充输入框 */}
              <ul className="mt-2 text-sm text-left list-disc list-inside space-y-2">
                <li 
                  className="my-1 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400"
                  onClick={() => setInputValue('针对合同负债科目，帮我找到：20240930相比于20231231合同负债的增长比例、以及20240930相比20240630合同负债增长比例，排名都是前5%的公司')}
                >
                  针对合同负债科目，帮我找到：20240930相比于20231231合同负债的增长比例、以及20240930相比20240630合同负债增长比例，排名都是前5%的公司
                </li>
                <li 
                  className="my-1 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400"
                  onClick={() => setInputValue('定义：自由现金流=经营活动产生的现金流量净额−购建固定资产、无形资产和其他长期资产支付的现金；帮我找到食品饮料行业中，20201231-20241231（年末1231）每年自由现金流都为正值的公司，并且把他们的累计值计算出来，从高到低列表排序给我')}
                >
                  定义：自由现金流=经营活动产生的现金流量净额−购建固定资产、无形资产和其他长期资产支付的现金；帮我找到食品饮料行业中，20201231-20241231（年末1231）每年自由现金流都为正值的公司，并且把他们的累计值计算出来，从高到低列表排序给我
                </li>
                <li 
                  className="my-1 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400"
                  onClick={() => setInputValue('以20240930为基准，找到存货周转率、资产周转率都比20230930高的公司列表，并且把20240930相比20230930提升的合计幅度最大的30家公司列出来')}
                >
                  以20240930为基准，找到存货周转率、资产周转率都比20230930高的公司列表，并且把20240930相比20230930提升的合计幅度最大的30家公司列出来
                </li>
                <li 
                  className="my-1 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400"
                  onClick={() => setInputValue('把20230331-20240930，一共5个季度，找到符合以下条件的公司：在这5个季度中，出现过连续3个季度：毛利率、净利率同时连续环比上升、资产负债率连续下降。把这些公司列出来给我。')}
                >
                  把20230331-20240930，一共5个季度，找到符合以下条件的公司：在这5个季度中，出现过连续3个季度：毛利率、净利率同时连续环比上升、资产负债率连续下降。把这些公司列出来给我。
                </li>
                {/* --- 新增问题 1 --- */}
                <li 
                  className="my-1 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400"
                  onClick={() => setInputValue('筛选20240630相比20231231同时满足以下条件的公司：毛利率、净利率提升；资产负债率下降；存货占总资产比例下降；经营性现金流净额/营业收入＞20%。输出毛利率提升幅度最大的10家公司。')}
                >
                  筛选20240630相比20231231同时满足以下条件的公司：毛利率、净利率提升；资产负债率下降；存货占总资产比例下降；经营性现金流净额/营业收入＞20%。输出毛利率提升幅度最大的10家公司。
                </li>
                {/* --- 结束新增问题 1 --- */}
                {/* --- 新增问题 2 --- */}
                <li 
                  className="my-1 cursor-pointer hover:text-blue-600 dark:hover:text-blue-400"
                  onClick={() => setInputValue('20240331-20240930为基准，找到过去3个季度毛利率、净利率连续提升的公司')}
                  >
                    20240331-20240930为基准，找到过去3个季度毛利率、净利率连续提升的公司
                </li>
                {/* --- 结束新增问题 2 --- */}
              </ul>
            </div>
          </div>
        )}
        
        {/* 消息列表 */}
        {displayMessages.map(message => (
          <Message
            key={message.id}
            content={message.content}
            isUser={message.isUser}
            timestamp={message.timestamp}
            contentType={message.contentType}
            filePath={message.filePath}
            error={message.error}
          />
        ))}
        
        {/* 使用ref元素让滚动条能自动定位到底部 */}
        <div ref={messagesEndRef} />
        
        {/* 如果有活动的查询进程，显示进度条 */}
        {displayProgress.isActive && (
          <div className="mb-4 mt-2 bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
            <div className="text-sm font-medium mb-2">
              {displayProgress.stage || '处理中...'}
            </div>
            <ProgressBar progress={displayProgress.progress} />
          </div>
        )}
      </div>
      
      {/* 输入区域 */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <ChatInput 
          // --- 修改: 传递状态和更新函数给 ChatInput ---
          value={inputValue} 
          onValueChange={setInputValue} 
          onSendMessage={handleSendMessage} 
          // --- 结束修改 ---
          disabled={isSendingMessage || mockProgress.isActive}
          placeholder={
            isSendingMessage || mockProgress.isActive 
              ? "正在处理您的请求..." 
              : "输入您的问题..."
          }
        />
      </div>
      
      {/* 使用模拟消息的提示(仅开发模式) */}
      {mockMessages.length > 0 && process.env.NODE_ENV === 'development' && (
        <div className="p-2 text-xs text-center bg-yellow-100 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-100">
          当前正在使用模拟API响应 (仅开发环境)
        </div>
      )}
    </div>
  );
};

export default ChatInterface; 