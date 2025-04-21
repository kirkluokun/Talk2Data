import { useCallback } from 'react';
import useAuth from '../hooks/useAuth';
import Layout from '../components/layout/Layout';

const HomePage = () => {
  const { user, logout } = useAuth();

  const handleLogout = useCallback(() => {
    logout();
    // 注意：路由重定向会在AuthContext的logout函数中自动处理
  }, [logout]);

  return (
    <div className="h-full w-full">
      <Layout />
    </div>
  );
}

export default HomePage; 