import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { TranscriptMessage } from '../types';

interface ChatBubbleProps {
  message: TranscriptMessage;
  piInitials?: string;
}

export default function ChatBubble({ message, piInitials = 'PI' }: ChatBubbleProps) {
  const isPI = message.role === 'pi';

  if (isPI) {
    return (
      <div className="flex items-start gap-3 mb-5">
        <div className="w-9 h-9 rounded-full bg-forest text-ivory flex items-center justify-center font-display text-sm font-medium shrink-0">
          {piInitials}
        </div>
        <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-bone border border-line px-4 py-3 shadow-[0_8px_24px_-12px_rgba(21,23,26,0.12)]">
          <div className="text-sm text-ink leading-relaxed [&_p]:mb-2 [&_p:last-child]:mb-0">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                strong: ({ children }) => (
                  <strong className="font-medium text-forest-dark">{children}</strong>
                ),
                em: ({ children }) => <em className="italic text-muted">{children}</em>,
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-forest underline decoration-forest/40 underline-offset-2 hover:decoration-forest"
                  >
                    {children}
                  </a>
                ),
                code: ({ children }) => (
                  <code className="bg-forest-soft text-forest-dark px-1 py-0.5 rounded text-xs font-mono">
                    {children}
                  </code>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside mb-2 space-y-0.5">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside mb-2 space-y-0.5">{children}</ol>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 mb-5 flex-row-reverse">
      <div className="w-9 h-9 rounded-full bg-ink/10 text-ink flex items-center justify-center text-xs font-medium shrink-0">
        You
      </div>
      <div className="max-w-[85%] rounded-2xl rounded-tr-sm bg-forest text-ivory px-4 py-3 shadow-[0_8px_24px_-12px_rgba(47,74,58,0.4)]">
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}
