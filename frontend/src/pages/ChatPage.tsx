import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

import { Header } from '@/components/layout/Header';
import { ChatInput } from '@/components/features/chat/ChatInput';
import { MessageList } from '@/components/features/chat/MessageList';
import { UserMessage } from '@/components/features/chat/UserMessage';
import { AssistantMessage } from '@/components/features/chat/AssistantMessage';
import { ThinkingIndicator } from '@/components/features/chat/ThinkingIndicator';
import { EmptyState } from '@/components/features/chat/EmptyState';

import { logger } from '@/lib/logger';
import type { Message, Citation } from '@/types';

import { useAuth } from '@/hooks/useAuth';
import { useModels, type Model } from '@/hooks/useModels';
import { useSessionMessages } from '@/hooks/useSessionMessages';
import { useSendMessage } from '@/hooks/useSendMessage';

const ChatPage = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  // Local state for messages (includes optimistic updates)
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [useGraph, setUseGraph] = useState(false);

  // Data Fetching
  const { data: models = [] } = useModels();
  const { data: historyMessages } = useSessionMessages(sessionId);
  const sendMessageMutation = useSendMessage();

  // Derive active model from fetched models
  const activeModelId = useMemo(() =>
    (models as Model[]).find(m => m.is_active)?.id || (models[0]?.id || ''),
    [models]
  );

  // Sync history to messages when session changes or loads
  useEffect(() => {
    if (historyMessages) {
      setMessages(historyMessages);
    } else if (!sessionId) {
      // Clear messages if no session
      setMessages([]);
    }
  }, [historyMessages, sessionId]);

  const handleSend = async (message: string) => {
    if (!message.trim()) return;

    // 1. Optimistic Update: User Message
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: message };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    try {
      // 2. Persist & Get Response
      const data = await sendMessageMutation.mutateAsync({
        message,
        sessionId,
        modelId: activeModelId || undefined,
        use_graph: useGraph
      });

      // 3. Update URL if new session
      if (data.session_id && !sessionId) {
        navigate(`/chat/${data.session_id}`, { replace: true });
      }

      // 4. Append Assistant Response
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        citations: data.citations?.map((c: Citation, i: number) => ({
          id: `c${i}`,
          source: c.source,
          page: c.page,
          text: c.text
        }))
      };
      setMessages(prev => [...prev, aiMsg]);
      logger.info("assistant_message_received", { citations: aiMsg.citations?.length });

    } catch (error: unknown) {
      logger.error("chat_request_failed", error as Error);
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

  const handleSuggestionClick = (prompt: string) => {
    handleSend(prompt);
  };

  return (
    <div className="flex flex-col h-full bg-background relative overflow-hidden">
      {/* Header */}
      <Header />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative min-h-0">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-4 animate-in fade-in duration-700">
            <EmptyState onSuggestionClick={handleSuggestionClick} />
            <ChatInput
              onSend={handleSend}
              disabled={isProcessing}
              isProcessing={isProcessing}
              onStop={() => setIsProcessing(false)}
              className="max-w-4xl w-full"
              useGraph={useGraph}
              onToggleGraph={() => setUseGraph(!useGraph)}
            />
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-hidden relative flex flex-col">
              <MessageList messages={messages} isProcessing={isProcessing}>
                {messages.map((m) => (
                  <div>
                    {m.role === 'user' ? (
                      <UserMessage
                        content={m.content}
                        userName={user?.name || "User"}
                      />
                    ) : (
                      <AssistantMessage
                        content={m.content}
                        citations={m.citations}
                        onRegenerate={() => handleSend(messages[messages.length - 2]?.content || '')}
                      />
                    )}
                  </div>
                ))}
                {isProcessing && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <ThinkingIndicator />
                  </motion.div>
                )}
              </MessageList>
            </div>

            <ChatInput
              onSend={handleSend}
              disabled={isProcessing}
              isProcessing={isProcessing}
              onStop={() => setIsProcessing(false)}
              useGraph={useGraph}
              onToggleGraph={() => setUseGraph(!useGraph)}
            />
          </>
        )}
      </div>
    </div>
  );
};


export default ChatPage;
