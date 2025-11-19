import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import { GroqAdapter } from "@copilotkit/runtime";

function sanitizeMessages(messages: any[]): any[] {
  if (!Array.isArray(messages)) return messages;

  return messages.map(msg => {
    // 🧠 Fix for assistant messages that contain toolCalls
    if (msg.role === 'assistant' && msg.toolCalls) {
      const fixedToolCalls = msg.toolCalls.map((tc: any) => ({
        ...tc,
        args: tc.args === null || tc.args === undefined ? {} : tc.args
      }));
      return { ...msg, toolCalls: fixedToolCalls };
    }

    // 🧠 Fix for ActionExecutionMessage type
    if (msg.type === 'ActionExecutionMessage') {
      return {
        ...msg,
        name: msg.name || 'policy_qa_agent',
        arguments: msg.arguments === null || msg.arguments === undefined ? {} : msg.arguments
      };
    }

    return msg;
  });
}

// Create the runtime with remote endpoint pointing to our FastAPI backend
const runtime = new CopilotRuntime({
  remoteEndpoints: [
    {
      url: process.env.NEXT_PUBLIC_COPILOT_BACKEND_URL || "http://127.0.0.1:8000/copilotkit",
    },
    
  ],
  
});

export const POST = async (req: NextRequest) => {
   //Create OpenAI adapter for the LLM
   const serviceAdapter = new OpenAIAdapter({ model: "gpt-3.5-turbo"});

  //const serviceAdapter = new GroqAdapter({model: "llama-3.1-8b-instant"});
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  try {
    const body = await req.json();
    
    if (body.messages) {
      console.log("🔍 Sanitizing messages in Next.js API route");
      body.messages = sanitizeMessages(body.messages);
    }
    
    // Create new request with sanitized body
    const sanitizedReq = new Request(req.url, {
      method: req.method,
      headers: req.headers,
      body: JSON.stringify(body),
    });
    
    return handleRequest(sanitizedReq as any);
  } catch (error) {
    console.error("❌ Error sanitizing request:", error);
    return handleRequest(req);
  }
};

// import {
//   CopilotRuntime,
//   OpenAIAdapter,
//   copilotRuntimeNextJSAppRouterEndpoint,
// } from "@copilotkit/runtime";
// import { NextRequest } from "next/server";

// // ✅ Create runtime that properly forwards headers
// const runtime = new CopilotRuntime({
//   remoteEndpoints: [
//     {
//       url: process.env.NEXT_PUBLIC_COPILOT_BACKEND_URL || "http://127.0.0.1:8000/copilotkit",
//     },
//   ],
// });

// export const POST = async (req: NextRequest) => {
//   console.log("🔍 Next.js API Route - Incoming Request");
  
//   try {
//     // Clone request to read body
//     const body = await req.clone().json();
    
//     console.log("📦 Request details:");
//     console.log("   URL:", req.url);
//     console.log("   Method:", req.method);
//     console.log("   Custom Headers:");
//     console.log("     X-User-Id:", req.headers.get('x-user-id'));
//     console.log("     X-User-Email:", req.headers.get('x-user-email'));
//     console.log("     X-User-Name:", req.headers.get('x-user-name'));
//     console.log("     X-Thread-Id:", req.headers.get('x-thread-id'));
    
//     console.log("   Body preview:", JSON.stringify(body).substring(0, 200));
//   } catch (error) {
//     console.log("❌ Could not parse request for debugging:", error);
//   }

//   // Create OpenAI adapter
//   const serviceAdapter = new OpenAIAdapter();
  
//   const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
//     runtime,
//     serviceAdapter,
//     endpoint: "/api/copilotkit",
//   });

//   // ✅ Forward the request with all headers preserved
//   return handleRequest(req);
// };

// // ✅ Also handle OPTIONS for CORS preflight
// export const OPTIONS = async (req: NextRequest) => {
//   return new Response(null, {
//     status: 200,
//     headers: {
//       'Access-Control-Allow-Origin': '*',
//       'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
//       'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-User-Id, X-User-Email, X-User-Name, X-Thread-Id',
//     },
//   });
// };


