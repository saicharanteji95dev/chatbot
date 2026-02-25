import { NextRequest } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL;

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

      // Check if the user explicitly asked for a contact form
      const lastUserMessage = trimmedMessages
        .filter((m: any) => m.role === "user")
        .at(-1)?.content?.toLowerCase() || "";

      const userRequestedForm =
        lastUserMessage.includes("contact form") ||
        lastUserMessage.includes("contact us") ||
        lastUserMessage.includes("contact you") ||
        lastUserMessage.includes("contact i95dev") ||
        lastUserMessage.includes("contact someone") ||
        lastUserMessage.includes("how to contact") ||
        lastUserMessage.includes("how can i contact") ||
        lastUserMessage.includes("how do i contact") ||
        lastUserMessage.includes("get in touch") ||
        lastUserMessage.includes("reach out") ||
        lastUserMessage.includes("talk to someone") ||
        lastUserMessage.includes("talk to a human") ||
        lastUserMessage.includes("speak to someone") ||
        lastUserMessage.includes("speak to an agent") ||
        lastUserMessage.includes("contact support") ||
        lastUserMessage.includes("contact sales") ||
        lastUserMessage.includes("i want to contact") ||
        lastUserMessage.includes("show me the form") ||
        lastUserMessage.includes("fill a form") ||
        lastUserMessage.includes("fill the form") ||
        lastUserMessage.includes("send a message") ||
        lastUserMessage.includes("give me a form") ||
        lastUserMessage.includes("i need a form") ||
        lastUserMessage.includes("submit a form") ||
        lastUserMessage.includes("book a meeting") ||
        lastUserMessage.includes("schedule a call") ||
        lastUserMessage.includes("request a demo") ||
        (/\bform\b/.test(lastUserMessage) && /\bcontact\b/.test(lastUserMessage));

      // Also detect when the LLM itself signals it's showing a form
      const assistantSignaledForm =
        lower.includes("contact form has been provided") ||
        lower.includes("a contact form") ||
        lower.includes("form has been provided") ||
        lower.includes("provided below for you to get in touch");

      if (
        userRequestedForm ||
        assistantSignaledForm ||
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
