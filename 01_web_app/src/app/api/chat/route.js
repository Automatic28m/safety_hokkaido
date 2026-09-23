import { NextResponse } from 'next/server';

export const maxDuration = 60; 

const backendApiUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000';

export async function POST(req) {
    try {
        const payload = await req.json();

        console.log("Next.js Proxy: Forwarding user query and history to Python Agentic RAG Backend...");
        
        try {
            const ragResponse = await fetch(`${backendApiUrl}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const ragData = await ragResponse.json();
            return NextResponse.json({ reply: ragData.reply });
            
        } catch (backendError) {
            console.error("Python Backend is down:", backendError);
            return NextResponse.json({ 
                reply: "Sorry, my Hokkaido Knowledge Engine is currently offline. Please ensure the Python backend is running on port 8000!" 
            });
        }
    } catch (error) {
        console.error("Chat API Error:", error);
        return NextResponse.json({ reply: error.message }, { status: 500 });
    }
}
