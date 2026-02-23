// Example usage in assistant UI (e.g., in assistant.tsx)
import { storeConversation } from '@/lib/conversationApi';

// ...existing code...

// Define types for example usage
type Message = {
  id: string;
  content: string;
  role: string;
  timestamp?: string;
};

async function handleSendMessage(messages: Message[], sessionId: string) {
  try {
    await storeConversation(messages, sessionId);
    // Optionally update UI or notify user
  } catch (error) {
    console.error('Error storing conversation:', error);
  }
}

// Call handleSendMessage after sending/receiving a message
// handleSendMessage(currentMessages, currentSessionId);

// ...existing code...
