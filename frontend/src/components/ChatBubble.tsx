import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { TranscriptMessage } from '../types';

interface ChatBubbleProps {
  message: TranscriptMessage;
  piName?: string;
}

export default function ChatBubble({ message, piName }: ChatBubbleProps) {
  const isPI = message.role === 'pi';

  return (
    <div className={`flex ${isPI ? 'justify-start' : 'justify-end'} mb-4`}>
      <div className={`max-w-[75%] ${isPI ? 'order-2' : ''}`}>
        <div className={`text-xs font-medium mb-1 ${isPI ? 'text-gray-500' : 'text-violet-500 text-right'}`}>
          {isPI ? (piName ?? 'PI') : 'You'}
        </div>
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
            isPI
              ? 'bg-gray-100 text-gray-800 rounded-tl-sm'
              : 'bg-violet-600 text-white rounded-tr-sm'
          }`}
        >
          {isPI ? (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                em: ({ children }) => <em className="italic">{children}</em>,
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline text-violet-700 hover:text-violet-900"
                  >
                    {children}
                  </a>
                ),
                ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-0.5">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-0.5">{children}</ol>,
                li: ({ children }) => <li className="ml-2">{children}</li>,
                code: ({ children }) => (
                  <code className="bg-gray-200 text-gray-800 px-1 py-0.5 rounded text-xs font-mono">{children}</code>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          ) : (
            message.content
          )}
        </div>
      </div>
    </div>
  );
}
