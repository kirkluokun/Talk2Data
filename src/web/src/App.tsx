import { AppRouter } from './routes';
import { AuthProvider } from './contexts/AuthContext';
import { ChatProvider } from './contexts/ChatContext';
// import Navbar from './components/layout/Navbar';

/**
 * 应用程序根组件
 * 提供认证和聊天上下文
 */
function App() {
  return (
    <AuthProvider>
      <ChatProvider>
        {/* 嵌套ChatProvider提供全局聊天状态 */}
        <AppRouter />
      </ChatProvider>
    </AuthProvider>
  );
}

export default App;
