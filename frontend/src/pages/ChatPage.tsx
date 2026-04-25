import { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { simulate, evaluate, getMatch, type SimulateResponse } from '../api/client';
import type { MatchResult, TranscriptMessage } from '../types';
import ChatBubble from '../components/ChatBubble';

export default function ChatPage() {
  const { matchId } = useParams<{ matchId: string }>();
  const navigate = useNavigate();

  const [match, setMatch] = useState<MatchResult | null>(null);
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState('');

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!matchId) return;
    loadMatch();
  }, [matchId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function loadMatch() {
    try {
      const data = await getMatch(Number(matchId));
      setMatch(data);
      if (data.transcript && data.transcript.length > 0) {
        setMessages(data.transcript);
      }
    } catch {
      setError('Could not load conversation. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSend() {
    if (!input.trim() || !matchId || sending) return;
    const userMessage: TranscriptMessage = { role: 'student', content: input.trim() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setSending(true);
    setError('');

    try {
      const updated: SimulateResponse = await simulate(Number(matchId), userMessage.content);
      if (updated.transcript) {
        setMessages(updated.transcript);
      }
    } catch {
      setError('Failed to send message. Check that the backend is running.');
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setSending(false);
    }
  }

  async function handleEvaluate() {
    if (!matchId) return;
    setEvaluating(true);
    setError('');
    try {
      await evaluate(Number(matchId));
      navigate(`/report/${matchId}`);
    } catch {
      setError('Evaluation failed. Make sure you have a conversation first.');
      setEvaluating(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const piName = match?.pi?.name ?? 'PI Avatar';

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <Link to={`/matches/${match?.student_id ?? ''}`} className="text-sm text-violet-600 hover:underline">
            ← Back
          </Link>
          <div className="w-px h-4 bg-gray-200" />
          <div>
            <div className="font-semibold text-gray-900 text-sm">{piName}</div>
            {match?.pi && (
              <div className="text-xs text-gray-400">{match.pi.department} · {match.pi.institution}</div>
            )}
          </div>
        </div>
        <button
          onClick={handleEvaluate}
          disabled={evaluating || messages.length < 2}
          className="bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
        >
          {evaluating ? 'Evaluating...' : 'Get Chemistry Report →'}
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 max-w-2xl mx-auto w-full">
        {loading && (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-3 border-violet-600 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {!loading && messages.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <div className="text-4xl mb-3">💬</div>
            <p className="font-medium text-gray-500">Start a conversation</p>
            <p className="text-sm mt-1">Ask {piName} about their research, lab culture, or funding opportunities.</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatBubble key={i} message={msg} piName={piName} />
        ))}

        {sending && (
          <div className="flex justify-start mb-4">
            <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Error */}
      {error && (
        <div className="mx-4 mb-2 bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-2 text-sm max-w-2xl mx-auto w-full">
          {error}
        </div>
      )}

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-4 py-3 sticky bottom-0">
        <div className="max-w-2xl mx-auto flex gap-2">
          <textarea
            rows={1}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={sending}
            placeholder="Type a message... (Enter to send)"
            className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:bg-gray-50"
          />
          <button
            onClick={handleSend}
            disabled={sending || !input.trim()}
            className="bg-violet-600 hover:bg-violet-700 disabled:bg-violet-300 text-white px-4 py-2.5 rounded-xl transition-colors font-medium text-sm"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-400 text-center mt-1.5">
          This is an AI avatar of {piName} — not the real person.
        </p>
      </div>
    </div>
  );
}
