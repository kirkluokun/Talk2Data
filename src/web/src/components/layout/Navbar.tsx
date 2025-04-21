import { Link } from 'react-router-dom';
import useAuth from '../../hooks/useAuth';

/**
 * 顶部导航栏组件
 * 显示用户登录状态、用户名和登出按钮
 */
const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuth();

  return (
    <nav className="bg-white shadow">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-indigo-600">
              Talk2FinancialData
            </Link>
          </div>

          <div className="flex items-center">
            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <span className="text-gray-700">
                  欢迎，{user?.username || '用户'}
                </span>
                <button
                  onClick={logout}
                  className="px-3 py-1 rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none"
                >
                  登出
                </button>
              </div>
            ) : (
              <div className="space-x-4">
                <Link
                  to="/login"
                  className="px-3 py-1 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100"
                >
                  登录
                </Link>
                <Link
                  to="/register"
                  className="px-3 py-1 rounded-md text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
                >
                  注册
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 