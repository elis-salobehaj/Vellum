import { useState, useRef, useEffect } from 'react';
import { config } from '../config';
import { useParams, useNavigate } from 'react-router-dom';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from '../authConfig';

import MessageBubble from '../components/Chat/MessageBubble';
import SourcePanel from '../components/Chat/SourcePanel';
import ChatInput from '../components/Chat/ChatInput';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
}

const ChatPage = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { instance, accounts } = useMsal();

  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: 'Hello! I am Vellum. How can I help you analyze your documents today?' }
  ]);
  const [selectedSource, setSelectedSource] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (scrollContainerRef.current) {
      const { scrollHeight, clientHeight } = scrollContainerRef.current;
      scrollContainerRef.current.scrollTo({
        top: scrollHeight - clientHeight + 100, // Add buffer to ensure bottom
        behavior: "smooth"
      });
    } else {
      // Fallback
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  };
  useEffect(scrollToBottom, [messages]);

  // Load History
  useEffect(() => {
    const loadHistory = async () => {
      if (sessionId) {
        try {
          const account = accounts[0];
          let token = "mock-token";
          if (account) {
            const response = await instance.acquireTokenSilent({
              ...loginRequest,
              account: account
            });
            token = response.accessToken;
          }

          // Fetch history for this session
          const res = await fetch(`${config.apiUrl}/history/${sessionId}`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          const data = await res.json();

          if (Array.isArray(data) && data.length > 0) {
            // Map backend messages to frontend format
            const mapped = data.map((msg: any, idx: number) => ({
              id: `hist-${idx}`,
              role: msg.role,
              content: msg.content,
              citations: msg.citations?.map((c: any, i: number) => ({
                id: `hist-${idx}-${i}`,
                source: c.source,
                page: c.page,
                text: c.text
              })) || []
            }));
            setMessages(mapped);
          } else if (data.length === 0) {
            // New or empty session
            setMessages([{ id: '1', role: 'assistant', content: 'Hello! I am Vellum. How can I help you analyze your documents today?' }]);
          }
        } catch (err) {
          console.error("Error fetching history", err);
        }
      } else {
        // Reset to default if no session ID
        setMessages([{ id: '1', role: 'assistant', content: 'Hello! I am Vellum. How can I help you analyze your documents today?' }]);
      }
    };
    loadHistory();
  }, [sessionId, instance, accounts]);

  const handleSend = async (message: string) => {
    if (!message.trim()) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: message };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    try {
      const account = accounts[0];
      let token = "mock-token";
      if (account) {
        const response = await instance.acquireTokenSilent({
          ...loginRequest,
          account: account
        });
        token = response.accessToken;
      }

      const response = await fetch(`${config.apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: message,
          model_id: null,
          session_id: sessionId // Pass session ID
        })
      });

      if (!response.ok) throw new Error('Failed to fetch response');
      const data = await response.json();

      // If we started a new session, update URL
      if (data.session_id && !sessionId) {
        navigate(`/chat/${data.session_id}`, { replace: true });
      }

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        citations: data.citations?.map((c: any, i: number) => ({
          id: `c${i}`,
          source: c.source,
          page: c.page,
          text: c.text
        }))
      };
      setMessages(prev => [...prev, aiMsg]);

    } catch (error) {
      console.error(error);
      const errorMsg: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: "Sorry, I encountered an error communicating with the server."
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex h-full overflow-hidden relative">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full relative">
        <div ref={scrollContainerRef} className="flex-1 overflow-y-auto p-4 space-y-6 scroll-smooth">
          {messages.map(m => (
            <MessageBubble
              key={m.id}
              message={m}
              onCitationClick={setSelectedSource}
            />
          ))}
          {isProcessing && (
            <div className="text-center text-sm text-gray-400 animate-pulse">Thinking...</div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-white border-t border-gray-100 z-10 relative">
          <ChatInput onSend={handleSend} disabled={isProcessing} />
          <div className="max-w-3xl mx-auto mt-2 text-center text-xs text-gray-400">
            AI can make mistakes. Please verify important information.
          </div>
        </div>
      </div>

      {/* Right Panel (Sources) */}
      {selectedSource && (
        <SourcePanel source={selectedSource} onClose={() => setSelectedSource(null)} />
      )}
    </div>
  );
};

export default ChatPage;
