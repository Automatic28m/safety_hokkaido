'use client';

import Image from 'next/image';
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

export default function ChatBot({ isOpen, onClose }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);

  // Initialize first message on mount to avoid hydration mismatch with timestamps
  useEffect(() => {
    setMessages([
      {
        role: 'ai',
        content: "Hi! I'm Tamago, your Hokkaido AI Guide. Ask me anything about disaster procedures or weather!",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ]);
  }, []);

  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      scrollToBottom();
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) scrollToBottom();
  }, [messages, isLoading, isOpen]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = { 
      role: 'user', 
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    const newMessages = [...messages, userMsg];
    
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          messages: newMessages,
          enabled_agents: { weather: true, disaster: true }
        })
      });
      
      const data = await response.json();
      
      setMessages([...newMessages, {
        role: 'ai',
        content: data.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } catch (error) {
      console.error("Chat Error:", error);
      setMessages([...newMessages, {
        role: 'ai',
        content: "Sorry, I couldn't connect to the server right now.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Blurred Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[90]" 
        onClick={onClose} 
        aria-hidden="true"
      />
      
      <div className="fixed top-6 bottom-8 left-[5%] right-[5%] sm:top-auto sm:left-auto sm:bottom-4 sm:right-4 sm:w-[400px] sm:h-[85vh] bg-white rounded-3xl shadow-2xl z-[100] flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-b from-[#0c59cc] to-[#1bb38e] pt-6 pb-5 px-6 flex items-center justify-between relative shrink-0 shadow-md z-10">
        
        {/* Left Side: Avatar & Info */}
        <div className="flex items-center gap-4">
          <div className="relative">
            <div className="w-[72px] h-[72px] relative bg-white rounded-full overflow-hidden shadow-sm border-[3px] border-white">
              <Image src="/illustrations/AI Profile.png" alt="Tamago" fill className="object-cover" />
            </div>
            {/* Online Dot */}
            <div className="absolute top-0 right-1 w-4 h-4 bg-[#34d399] border-2 border-[#0f60c2] rounded-full shadow-sm"></div>
          </div>
          
          <div className="flex flex-col">
            <h2 className="text-white font-bold text-2xl tracking-wide leading-tight">Tamago</h2>
            <p className="text-white text-sm opacity-90 mt-0.5">Ready for answer</p>
          </div>
        </div>

        {/* Right Side: Close Button */}
        <button onClick={onClose} className="text-white p-2 hover:bg-white/20 rounded-full transition-colors self-start mt-2" aria-label="Close chat">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 p-4 overflow-y-auto overscroll-none bg-gray-50 flex flex-col gap-6">
        
        {messages.map((msg, index) => (
          <div key={index} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            
            {msg.role === 'user' ? (
              <div className="flex flex-col items-end gap-1.5 w-[90%]">
                <div className="px-6 py-4 rounded-3xl bg-[#0c4ca3] text-white w-full shadow-sm">
                  <div className="text-sm whitespace-pre-wrap">
                    {msg.content}
                  </div>
                </div>
                <span className="text-[11px] text-gray-400 font-medium tracking-wide mr-2">
                  {msg.timestamp}
                </span>
              </div>
            ) : (
              <div className="flex flex-col items-start gap-2 w-[90%]">
                <div className="px-6 py-4 rounded-3xl bg-gray-100 text-gray-800 w-full shadow-sm">
                  <div className="prose prose-sm prose-slate max-w-none prose-p:leading-relaxed prose-li:my-0.5">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                </div>
                <div className="flex items-center gap-2.5 ml-2">
                  <div className="w-10 h-10 relative rounded-full overflow-hidden shrink-0 shadow-sm border border-gray-200">
                    <Image src="/illustrations/AI Profile.png" alt="Tamago" fill className="object-cover" />
                  </div>
                  {msg.timestamp && (
                    <span className="text-[11px] text-gray-400 font-medium tracking-wide mt-1">
                      {msg.timestamp}
                    </span>
                  )}
                </div>
              </div>
            )}
            
          </div>
        ))}
        
        {isLoading && (
          <div className="flex w-full justify-start">
            <div className="flex flex-col items-start gap-2 w-[90%]">
              <div className="px-6 py-4 rounded-3xl bg-gray-100 shadow-sm w-full">
                <div className="flex gap-1.5 items-center h-full pt-1 pb-0.5">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                </div>
              </div>
              <div className="w-10 h-10 relative rounded-full overflow-hidden shrink-0 shadow-sm border border-gray-200 ml-2">
                <Image src="/illustrations/AI Profile.png" alt="Tamago" fill className="object-cover" />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-gray-50 shrink-0 pb-8 sm:pb-4">
        <form onSubmit={handleSubmit} className="bg-white border-2 border-gray-200 rounded-full flex items-center px-3 py-2 gap-3 shadow-sm">
          <button type="button" className="text-black p-2" aria-label="Add attachment">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          </button>
          
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder="Ask Tamago" 
            className="flex-1 bg-transparent outline-none min-w-0 text-lg placeholder:text-gray-300 text-gray-700" 
          />
          
          <button type="button" className="text-black p-2" aria-label="Voice input">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>
          </button>
          
          <button 
            type="submit" 
            disabled={isLoading || !input.trim()}
            className="w-12 h-12 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 hover:bg-orange-500 transition-colors disabled:opacity-50" 
            aria-label="Send message"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m12 19 0-14"/><path d="m5 12 7-7 7 7"/></svg>
          </button>
        </form>
      </div>
    </div>
    </>
  );
}
