import React from 'react';
import MarkdownRenderer from './MarkdownRenderer';
import DataTable from './DataTable';
import ImageViewer from './ImageViewer';
import api from '../../lib/axios';

type ContentDisplayProps = {
  content?: string;
  contentType?: string;
  filePath?: string;
  error?: string | null;
};

// ContentDisplay组件：根据内容类型动态选择渲染组件
const ContentDisplay: React.FC<ContentDisplayProps> = ({
  content,
  contentType,
  filePath,
  error,
}) => {
  // 处理文件下载
  const handleFileDownload = async (path: string) => {
    try {
      const filename = path.split('/').pop() || 'download';
      const response = await api.get(`/file/${path}`, {
        responseType: 'blob'
      });

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('文件下载失败:', err);
      alert('文件下载失败，请稍后再试');
    }
  };

  // 处理路径，移除可能的 ../ 前缀
  const processPath = (path: string): string => {
    if (!path) return '';
    
    // 移除开头的 ../ 或 ./
    return path.replace(/^\.\.\/|^\.\//g, '');
  };

  // 如果有错误，显示错误信息
  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-md">
        <p className="text-red-500 font-medium">处理出错</p>
        <p className="text-sm text-red-600 mt-1">{error}</p>
      </div>
    );
  }

  // 处理filePath路径
  const processedFilePath = filePath ? processPath(filePath) : '';

  // 根据内容类型选择渲染组件
  switch (contentType) {
    case 'text':
      // 文本类型，使用Markdown渲染器
      return <MarkdownRenderer content={content || '内容为空'} />;

    case 'dataframe_csv_path':
      // 数据表类型，使用DataTable组件
      if (!processedFilePath) {
        return <div className="text-yellow-600">无法显示表格：未提供文件路径</div>;
      }
      return <DataTable filePath={processedFilePath} />;

    case 'plot_file_path':
      // 图像类型，使用ImageViewer组件
      if (!processedFilePath) {
        return <div className="text-yellow-600">无法显示图像：未提供文件路径</div>;
      }
      return <ImageViewer imagePath={processedFilePath} />;
    
    default:
      // 默认或未知类型，尝试直接显示内容或提示
      if (content) {
        return <MarkdownRenderer content={content} />;
      }
      
      if (processedFilePath) {
        // 根据文件扩展名猜测类型
        if (processedFilePath.toLowerCase().match(/\.(png|jpg|jpeg|gif|svg)$/)) {
          return <ImageViewer imagePath={processedFilePath} />;
        }
        
        if (processedFilePath.toLowerCase().endsWith('.csv')) {
          return <DataTable filePath={processedFilePath} />;
        }
        
        return (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
            <p className="font-medium">文件已生成</p>
            <button 
              onClick={() => handleFileDownload(processedFilePath)}
              className="text-blue-600 hover:underline mt-1 inline-block"
            >
              点击下载: {processedFilePath.split('/').pop()}
            </button>
          </div>
        );
      }
      
      return <div className="text-gray-500 italic">未提供内容</div>;
  }
};

export default ContentDisplay; 