import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from '../authConfig';

import { Header } from '@/components/layout/Header';
import { ChatInput } from '@/components/Chat/ChatInput';
import { MessageList } from '@/components/Chat/MessageList';
import { UserMessage } from '@/components/Chat/UserMessage';
import { AssistantMessage } from '@/components/Chat/AssistantMessage';
import { ThinkingIndicator } from '@/components/Chat/ThinkingIndicator';
import { EmptyState } from '@/components/Chat/EmptyState';

import { config } from '@/config';
import { logger } from '@/lib/logger';
import type { Message } from '@/types';

interface Model {
  id: string;
  is_active: boolean;
  name?: string;
}

const ChatPage = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { instance, accounts } = useMsal();

  // Initial state is empty to show EmptyState first
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // State for Models
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');

  // Fetch Models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const account = accounts[0];
        let token = "mock-token";
        if (account) {
          const response = await instance.acquireTokenSilent({
            ...loginRequest,
            account: account
          });
          token = response.idToken;
        }

        const res = await fetch(`${config.apiUrl}/admin/models`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (res.ok) {
          const data = await res.json();
          logger.info("models_fetched", { count: data.length });
          setModels(data);
          // Default to active model or first
          const active = data.find((m: Model) => m.is_active);
          if (active) setSelectedModel(active.id);
          else if (data.length > 0) setSelectedModel(data[0].id);
        }
      } catch (err) {
        logger.error("models_fetch_failed", err);
      }
    };
    fetchModels();
  }, [instance, accounts]);

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
            token = response.idToken;
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
          }
          logger.info("history_loaded", { sessionId, messageCount: data.length });
        } catch (err) {
          logger.error("history_load_failed", { sessionId, error: err });
        }
      } else {
        setMessages([]);
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
        token = response.idToken;
      }

      const res = await fetch(`${config.apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: message,
          model_id: selectedModel || null,
          session_id: sessionId
        })
      });

      if (!res.ok) throw new Error('Failed to fetch response');
      const data = await res.json();

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
      logger.info("assistant_message_received", { citations: aiMsg.citations?.length });

    } catch (error) {
      logger.error("chat_request_failed", error);
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
            {messages.map((m) => (
              m.role === 'user' ? (
                <UserMessage
                  key={m.id}
                  content={m.content}
                  userName={accounts[0]?.name}
                />
              ) : (
                <AssistantMessage
                  key={m.id}
                  content={m.content}
                  citations={m.citations}
                  onRegenerate={() => handleSend(messages[messages.length - 2]?.content || '')}
                />
              )
            ))}
            {isProcessing && <ThinkingIndicator />}
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
