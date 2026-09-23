'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useState } from 'react';
import ChatBot from './ChatBot';

export default function FloatingButtons() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  return (
    <>
      <div className="fixed bottom-6 right-4 z-40 flex flex-col gap-8 items-center">
        {/* Emergency Contact */}
        <Link href="/emergency-contact" className="relative group transition-all duration-300 hover:scale-110 hover:-translate-y-2 hover:drop-shadow-2xl active:scale-95 flex flex-col items-center">
          {/* Arced Text SVG */}
          <svg viewBox="0 0 100 100" className="absolute top-[45%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120px] h-[120px] pointer-events-none z-10 overflow-visible">
            <path id="emergency-curve" d="M 5,60 A 45,45 0 1,1 95,60" fill="transparent" />
            <text 
              className="text-[16px] font-black" 
              fill="black" 
              stroke="white" 
              strokeWidth="4" 
              strokeLinejoin="round"
              paintOrder="stroke fill"
            >
              <textPath href="#emergency-curve" startOffset="50%" textAnchor="middle">
                contact
              </textPath>
            </text>
          </svg>

          <div className="w-16 h-16 relative rounded-full overflow-hidden shadow-xl shadow-black/40 border-[3px] border-white bg-orange-500">
             <Image 
               src="/illustrations/AI Emergency.png" 
               alt="Emergency Contact" 
               fill 
               className="object-cover"
             />
          </div>
        </Link>

        {/* AI Chat */}
        <button 
          onClick={() => setIsChatOpen(true)}
          className="relative group transition-all duration-300 hover:scale-110 hover:-translate-y-2 hover:drop-shadow-2xl active:scale-95 flex flex-col items-center"
        >
          {/* Arced Text SVG */}
          <svg viewBox="0 0 100 100" className="absolute top-[45%] left-1/2 -translate-x-1/2 -translate-y-1/2 w-[110px] h-[110px] pointer-events-none z-10 overflow-visible">
            <path id="ai-curve" d="M 15,55 A 35,35 0 1,1 85,55" fill="transparent" />
            <text 
              className="text-[16px] font-black" 
              fill="black" 
              stroke="white" 
              strokeWidth="4" 
              strokeLinejoin="round"
              paintOrder="stroke fill"
            >
              <textPath href="#ai-curve" startOffset="50%" textAnchor="middle">
                AI chat
              </textPath>
            </text>
          </svg>

          <div className="w-16 h-16 relative rounded-full overflow-hidden shadow-xl shadow-black/40 border-[3px] border-white bg-blue-500">
             <Image 
               src="/illustrations/AI Profile.png" 
               alt="AI Chat" 
               fill 
               className="object-cover"
             />
          </div>
        </button>
      </div>

      {/* The ChatBot Popup */}
      <ChatBot isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </>
  );
}
