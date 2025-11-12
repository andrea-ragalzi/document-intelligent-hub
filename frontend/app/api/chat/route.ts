export const runtime = "edge";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/rag";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export async function POST(req: Request) {
  try {
    const { messages, userId } = await req.json();

    if (!userId) {
      return new Response("User ID is required", { status: 400 });
    }

    // Extract the last user query
    const lastMessage = messages[messages.length - 1] as Message;
    if (!lastMessage || lastMessage.role !== "user") {
      return new Response("Invalid message format", { status: 400 });
    }

    const userQuery = lastMessage.content;

    // Prepare history for the backend (exclude last message)
    const chatHistory = messages.slice(0, -1).map((msg: Message) => ({
      type: msg.role === "user" ? "user" : "assistant",
      text: msg.content,
    }));

    // Call the FastAPI backend
    const response = await fetch(`${API_BASE_URL}/query/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: userQuery,
        user_id: userId,
        chat_history: chatHistory,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return new Response(
        JSON.stringify({ error: errorData.detail || "Backend error" }),
        { status: response.status }
      );
    }

    const data = await response.json();

    // For now return the response as complete text
    const answer = data.answer || "No response available";
    const sources = data.source_documents || [];

    // Create a stream compatible with Vercel AI SDK
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        // Vercel AI SDK format: each chunk must start with "0:" for text content
        for (let i = 0; i < answer.length; i++) {
          const chunk = `0:${JSON.stringify(answer[i])}\n`;
          controller.enqueue(encoder.encode(chunk));
          // Small delay to simulate streaming
          await new Promise((resolve) => setTimeout(resolve, 10));
        }

        // Add sources as annotation (if needed)
        if (sources.length > 0) {
          const sourcesText = `\n\n📚 Sources: ${sources.join(", ")}`;
          for (const char of sourcesText) {
            const chunk = `0:${JSON.stringify(char)}\n`;
            controller.enqueue(encoder.encode(chunk));
            await new Promise((resolve) => setTimeout(resolve, 5));
          }
        }

        controller.close();
      },
    });

    return new Response(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
      },
    });
  } catch (error) {
    console.error("Chat API Error:", error);
    return new Response(JSON.stringify({ error: "Internal server error" }), {
      status: 500,
    });
  }
}
