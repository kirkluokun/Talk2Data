import { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';

interface ProtectedRouteProps {
  children: ReactNode;
}

/**
 * 路由保护组件
 * 确保只有已登录用户才能访问受保护的路由
 * 未登录用户将被重定向到登录页面
 */
const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  // 使用useAuth钩子获取认证状态
  const { isAuthenticated, isLoading } = useAuth();

  // 显示加载状态
  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center">加载中...</div>;
  }

  // 如果未认证，重定向到登录页
  if (!isAuthenticated) {
    console.log('未认证，重定向到登录页');
    return <Navigate to="/login" replace />;
  }

  // 已认证，显示子组件
  return <>{children}</>;
};

export default ProtectedRoute; 