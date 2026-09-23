'use client';

import { useState } from 'react';

export default function Accordion({ title, children }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={`bg-green-700 text-white rounded-2xl shadow-md transition-all duration-300 ${isOpen ? 'p-5' : 'py-3 px-6'}`}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex justify-between items-center font-bold text-lg focus:outline-none"
      >
        <span className="text-left">{title}</span>
        <svg 
          width="24" height="24" 
          viewBox="0 0 24 24" fill="none" stroke="currentColor" 
          strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"
          className={`transform transition-transform duration-300 shrink-0 ml-2 ${isOpen ? '' : 'rotate-180'}`}
        >
          <path d="m18 15-6-6-6 6"/>
        </svg>
      </button>
      
      <div 
        className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[800px] mt-4 opacity-100' : 'max-h-0 opacity-0'}`}
      >
        <div className="text-white">
          {children}
        </div>
      </div>
    </div>
  );
}
