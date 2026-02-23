import { NextRequest } from "next/server";

const BACKEND_URL =
  process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(req: NextRequest) {
  const { messages } = await req.json();

  const simpleMessages = messages.map((msg: any) => ({
    role: msg.role,
    content:
      typeof msg.content === "string"
        ? msg.content
        : msg.parts?.find((p: any) => p.type === "text")?.text || "",
  }));

  // 🔥 SHORT TERM MEMORY
  const MAX_HISTORY = 12;
  const trimmedMessages = simpleMessages.slice(-MAX_HISTORY);

  const backendResponse = await fetch(`${BACKEND_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages: trimmedMessages }),
  });

  const data = await backendResponse.json();
  const assistantMessage =
    data.content || data.message || "No response received.";

  const encoder = new TextEncoder();
  const messageId = crypto.randomUUID();

  const stream = new ReadableStream({
    async start(controller) {
      // Start
      controller.enqueue(
        encoder.encode(
          `data: ${JSON.stringify({
            type: "text-start",
            id: messageId,
          })}\n\n`
        )
      );

      // Stream word by word
      const words = assistantMessage.split(" ");
      for (const word of words) {
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({
              type: "text-delta",
              id: messageId,
              delta: word + " ",
            })}\n\n`
          )
        );
        await new Promise((r) => setTimeout(r, 20));
      }

      // End
      controller.enqueue(
        encoder.encode(
          `data: ${JSON.stringify({
            type: "text-end",
            id: messageId,
          })}\n\n`
        )
      );

      // 🔥 SAFE CONTACT FORM DETECTION
      const lower = assistantMessage.toLowerCase();

      if (
        lower.includes("don't have that information") ||
        lower.includes("do not have that information") ||
        lower.includes("based on the available data")
      ) {
        const toolCallId = crypto.randomUUID();

        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({
              type: "tool-input-available",
              toolCallId,
              toolName: "contact_form",
            })}\n\n`
          )
        );

        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({
              type: "tool-output-available",
              toolCallId,
            })}\n\n`
          )
        );
      }

      controller.enqueue(
        encoder.encode(`data: ${JSON.stringify({ type: "finish" })}\n\n`)
      );

      controller.close();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
