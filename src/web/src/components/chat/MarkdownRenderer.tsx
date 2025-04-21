import React from 'react';
import ReactMarkdown from 'react-markdown';

type MarkdownRendererProps = {
  content: string;
};

// MarkdownRenderer组件：用于渲染Markdown格式的文本
const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  return (
    <div className="markdown-renderer prose prose-sm max-w-none">
      <ReactMarkdown>
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer; 