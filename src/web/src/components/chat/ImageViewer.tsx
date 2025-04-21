import React, { useState, useEffect } from 'react';
import api from '../../lib/axios';

type ImageViewerProps = {
  imagePath: string;
  alt?: string;
};

// ImageViewer组件：用于显示图像文件
const ImageViewer: React.FC<ImageViewerProps> = ({ imagePath, alt = '分析图表' }) => {
  // 图像加载状态
  const [loading, setLoading] = useState(true);
  // 图像加载错误状态
  const [error, setError] = useState(false);
  // 图像URL状态
  const [imageUrl, setImageUrl] = useState<string>('');
  
  // 处理路径，移除可能的 ../ 前缀
  const processPath = (path: string): string => {
    // 移除开头的 ../ 或 ./
    let processedPath = path.replace(/^\.\.\/|^\.\//g, '');
    
    // 确保路径不以 output/ 或 /output/ 开头重复
    if (processedPath.startsWith('output/')) {
      return processedPath;
    } else if (processedPath.startsWith('/output/')) {
      return processedPath.substring(1); // 移除开头的斜杠
    }
    
    // 如果路径不包含 output，则添加前缀
    return `output/${processedPath}`;
  };

  // 获取图片Blob URL
  useEffect(() => {
    const loadImage = async () => {
      try {
        setLoading(true);
        setError(false);

        const processedPath = processPath(imagePath);
        const apiEndpoint = `/file/${processedPath}`;
        
        const response = await api.get(apiEndpoint, {
          responseType: 'blob'
        });
        
        // 创建Blob URL
        const blob = new Blob([response.data], { type: response.headers['content-type'] });
        const objectUrl = URL.createObjectURL(blob);
        
        setImageUrl(objectUrl);
        setLoading(false);
      } catch (err) {
        console.error('加载图像失败:', err);
        setError(true);
        setLoading(false);
      }
    };

    if (imagePath) {
      loadImage();
    }

    // 清理函数
    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
      }
    };
  }, [imagePath]);
  
  // 图像加载成功处理函数
  const handleImageLoad = () => {
    setLoading(false);
  };
  
  // 图像加载失败处理函数
  const handleImageError = () => {
    setLoading(false);
    setError(true);
  };
  
  // API端点
  const apiEndpoint = `/file/${processPath(imagePath)}`;
  
  return (
    <div className="my-4 flex justify-center">
      {loading && (
        <div className="flex justify-center items-center h-64 w-full">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      )}
      
      {error ? (
        <div className="p-4 text-center text-red-500 border border-red-200 rounded">
          <p>图像加载失败。请检查文件路径或稍后再试。</p>
          <p className="text-xs mt-2 text-gray-500">尝试访问: {apiEndpoint}</p>
        </div>
      ) : (
        <img
          src={imageUrl || null}
          alt={alt}
          className={`max-w-full h-auto rounded shadow-lg ${loading ? 'hidden' : 'block'}`}
          onLoad={handleImageLoad}
          onError={handleImageError}
        />
      )}
      
      {/* 图像控制按钮 */}
      {!loading && !error && (
        <div className="mt-2 text-center">
          <a
            href={imageUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            在新标签页中查看
          </a>
        </div>
      )}
    </div>
  );
};

export default ImageViewer; 