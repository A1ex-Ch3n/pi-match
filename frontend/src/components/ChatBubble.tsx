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
          {message.content}
        </div>
      </div>
    </div>
  );
}
