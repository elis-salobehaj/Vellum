import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';

import { Header } from '@/components/layout/Header';
import { ChatInput } from '@/components/Chat/ChatInput';
import { MessageList } from '@/components/Chat/MessageList';
import { UserMessage } from '@/components/Chat/UserMessage';
import { AssistantMessage } from '@/components/Chat/AssistantMessage';
import { ThinkingIndicator } from '@/components/Chat/ThinkingIndicator';
import { EmptyState } from '@/components/Chat/EmptyState';

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

  // Data Fetching
  const { data: models = [] } = useModels();
  const { data: historyMessages } = useSessionMessages(sessionId);
  const sendMessageMutation = useSendMessage();

  const [selectedModel, setSelectedModel] = useState<string>('');

  // Sync models to selectedModel
  useEffect(() => {
    if (models.length > 0 && !selectedModel) {
      const active = (models as Model[]).find((m) => m.is_active);
      if (active) setSelectedModel(active.id);
      else setSelectedModel(models[0].id);
    }
  }, [models, selectedModel]);

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
        modelId: selectedModel || undefined
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
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <Header
        models={models}
        selectedModel={selectedModel}
        onModelChange={setSelectedModel}
      />

      {/* Chat Area */}
      <div className="flex-1 overflow-hidden relative flex flex-col">
        {messages.length === 0 ? (
          <EmptyState onSuggestionClick={handleSuggestionClick} />
        ) : (
          <MessageList messages={messages} isProcessing={isProcessing}>
            <AnimatePresence initial={false} mode="popLayout">
              {messages.map((m) => (
                <motion.div
                  key={m.id}
                  initial={{ opacity: 0, y: 10, scale: 0.95 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  transition={{
                    duration: 0.3,
                    delay: 0.05,
                    ease: "easeOut"
                  }}
                  layout
                >
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
                </motion.div>
              ))}
            </AnimatePresence>
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
        )}
      </div>

      {/* Input Area */}
      <ChatInput
        onSend={handleSend}
        disabled={isProcessing}
        isProcessing={isProcessing}
        onStop={() => setIsProcessing(false)} // Placeholder for actual stop logic
      />
    </div>
  );
};

export default ChatPage;
