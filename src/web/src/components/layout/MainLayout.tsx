import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

/**
 * 主应用布局组件
 * 包含顶部导航栏和用于渲染子路由内容的 Outlet
 */
const MainLayout = () => {
  return (
    // 使用 flex-col 让 Navbar 和 main 垂直排列
    // h-screen 确保布局占满整个屏幕高度
    <div className="flex flex-col h-screen">
      <Navbar />
      {/* flex-grow 让 main 区域填充剩余空间 */}
      {/* overflow-hidden 防止内容溢出 */}
      <main className="flex-grow overflow-hidden">
        {/* Outlet 渲染 HomePage，HomePage 内部渲染 Layout */}
        <Outlet />
      </main>
    </div>
  );
};

export default MainLayout; 