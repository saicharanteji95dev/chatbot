// utils/conversationApi.ts
// Utility for storing chat conversations via API

// Define types for conversation messages
export type Message = {
  id: string;
  content: string;
  role: string;
  timestamp?: string;
};

export async function storeConversation(messages: Message[], sessionId: string) {
  const endpoint = process.env.NEXT_PUBLIC_API_ENDPOINT;
  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  const projectId = process.env.NEXT_PUBLIC_PROJECT_ID;


  // Only include X-Project-Id if projectId is defined
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${apiKey}`,
  };
  if (projectId) {
    headers['X-Project-Id'] = projectId;
  }

  const res = await fetch(`${endpoint}/conversations`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ sessionId, messages }),
  });

  if (!res.ok) {
    throw new Error('Failed to store conversation');
  }
  return res.json();
}
