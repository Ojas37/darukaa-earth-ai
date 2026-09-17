import { useState } from 'react';
import type { ChatMessage, ChatResponse } from './types/api';
import { sendChatMessage } from './services/api';
import { Header } from './components/Header';
import { ChatWindow } from './components/ChatWindow';
import { ChatInput } from './components/ChatInput';

export function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [turnCount, setTurnCount] = useState<number>(0);
  const [inputPrompt, setInputPrompt] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSubmitted, setLastSubmitted] = useState<string>('');

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend !== undefined ? textToSend : inputPrompt).trim();
    if (!query || isLoading) return;

    setError(null);
    setLastSubmitted(query);

    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: timeStr,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputPrompt('');
    setIsLoading(true);

    try {
      const responseData: ChatResponse = await sendChatMessage(query, conversationId);

      // Save conversation ID from backend
      if (responseData.conversation_id) {
        setConversationId(responseData.conversation_id);
      }
      if (responseData.turn_index !== undefined) {
        setTurnCount(responseData.turn_index);
      } else {
        setTurnCount((prev) => prev + 1);
      }

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: responseData.message || 'Ecological diagnostic analysis complete.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        response: responseData,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      console.error('Chat error:', err);
      setError(
        err.message ||
          'Failed to connect to the Darukaa reasoning service. Ensure the FastAPI backend is running at http://localhost:8000.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewAssessment = () => {
    setMessages([]);
    setConversationId(null);
    setTurnCount(0);
    setInputPrompt('');
    setError(null);
    setLastSubmitted('');
  };

  const handleSelectExample = (promptText: string) => {
    setInputPrompt(promptText);
  };

  const handleSelectClarificationHint = (hint: string) => {
    setInputPrompt((prev) => (prev ? `${prev} In response to "${hint}": ` : `Regarding "${hint}": `));
  };

  const handleRetry = () => {
    if (lastSubmitted) {
      handleSendMessage(lastSubmitted);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F7F2] text-[#17231D]">
      {/* Top Header */}
      <Header
        onNewAssessment={handleNewAssessment}
        conversationId={conversationId}
        turnCount={turnCount}
      />

      {/* Main Conversation Area */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          error={error}
          onSelectPrompt={handleSelectExample}
          onSelectClarificationHint={handleSelectClarificationHint}
          onRetry={handleRetry}
        />

        {/* Bottom Input Composer */}
        <ChatInput
          value={inputPrompt}
          onChange={setInputPrompt}
          onSubmit={() => handleSendMessage()}
          isLoading={isLoading}
          onClear={() => setInputPrompt('')}
        />
      </main>
    </div>
  );
}

export default App;
