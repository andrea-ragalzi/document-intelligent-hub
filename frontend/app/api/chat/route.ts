export const runtime = "nodejs";
export const maxDuration = 300;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/rag";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export async function POST(req: Request) {
  try {
    // Extract Authorization header from the incoming request
    const authHeader = req.headers.get("Authorization");
    if (!authHeader) {
      return new Response(JSON.stringify({ error: "Missing authorization token" }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }

    const { messages, userId, output_language } = await req.json();

    if (!userId) {
      return new Response("User ID is required", { status: 400 });
    }

    // Extract the last user query
    const lastMessage = messages[messages.length - 1] as Message;
    if (!lastMessage?.content || lastMessage.role !== "user") {
      return new Response("Invalid message format", { status: 400 });
    }

    const userQuery = lastMessage.content;

    // Prepare history for the backend, excluding the latest user message.
    const chatHistory = messages.slice(0, -1).map((msg: Message) => ({
      role: msg.role === "user" ? "user" : "assistant",
      content: msg.content,
    }));

    // Prepare request body
    const requestBody: Record<string, unknown> = {
      query: userQuery,
      user_id: userId,
      conversation_history: chatHistory,
    };

    if (output_language) {
      requestBody.output_language = output_language;
    }

    // Call the FastAPI backend
    const response = await fetch(`${API_BASE_URL}/query/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: authHeader,
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.detail || "Backend error";

      // Return error with appropriate status code (including 429)
      return new Response(JSON.stringify({ error: errorMessage }), {
        status: response.status,
        headers: { "Content-Type": "application/json" },
      });
    }

    const data = await response.json();

    let answer = data.answer || "No response available";

    // Clean up [DOCUMENT X] markers from the answer
    // These are internal reference markers that shouldn't appear in user-facing text
    answer = answer.replaceAll(/\s*\[DOCUMENT\s+\d+\]/gi, "");

    // Create a stream compatible with Vercel AI SDK
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        // Vercel AI SDK format: each chunk must start with "0:" for text content
        for (const char of answer) {
          const chunk = `0:${JSON.stringify(char)}\n`;
          controller.enqueue(encoder.encode(chunk));
          // Small delay to simulate streaming
          await new Promise(resolve => setTimeout(resolve, 10));
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
