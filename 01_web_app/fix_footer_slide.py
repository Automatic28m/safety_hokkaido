import re

with open('src/components/Footer.jsx', 'r') as f:
    content = f.read()

# I will rewrite Footer.jsx entirely to include a FooterAccordion component to handle the smooth slide.
new_footer = """'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';

// Reusable smooth accordion for the footer
const FooterAccordion = ({ title, children, defaultOpen = false, className = "" }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={className}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex justify-between items-center font-bold text-lg md:text-base mb-2 md:mb-3 hover:text-orange-300 transition-colors focus:outline-none group pr-4 md:pr-0"
      >
        <span className="text-left">{title}</span>
        <svg 
          className={`w-5 h-5 md:w-4 md:h-4 transform transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} 
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      <div 
        className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[300px] opacity-100' : 'max-h-0 opacity-0 md:max-h-0'}`}
      >
        <ul className="pl-6 md:pl-0 space-y-2 opacity-90 md:opacity-80 text-[15px] md:text-sm pb-4 md:pb-0">
          {children}
        </ul>
      </div>
    </div>
  );
};

export default function Footer() {
  const pathname = usePathname();
  const locale = pathname.split('/')[1] || 'en';
  
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="w-full pb-8 md:pb-12 bg-transparent flex justify-center mt-12 md:mt-24">
      <footer className="w-[92%] max-w-md md:max-w-6xl mx-auto bg-gradient-to-b from-[#0047b3] to-[#0c8a9e] text-white rounded-[24px] md:rounded-[32px] p-8 md:p-12 md:py-16 shadow-lg relative">
        
        {/* Mobile Layout */}
        <div className="md:hidden">
          <div className="flex justify-between items-start mb-8">
            <Link href={`/${locale}`}>
              <Image src="/illustrations/logo_team.png" alt="SafetyHokaido" width={100} height={50} className="w-[100px] h-auto" />
            </Link>
            <button 
              onClick={scrollToTop}
              aria-label="Back to top"
              className="w-10 h-10 bg-orange-400 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-105 active:scale-95 shrink-0"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m18 15-6-6-6 6"/>
              </svg>
            </button>
          </div>

          <nav className="space-y-4">
            <div className="mb-4">
              <Link href={`/${locale}`} className="font-bold text-lg hover:text-orange-300 transition-colors">Top</Link>
            </div>
            
            <FooterAccordion title="Disaster">
              <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/disaster/blizzard`} className="block w-full">Blizzard</Link></li>
              <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/disaster/earthquake`} className="block w-full">Earthquake</Link></li>
            </FooterAccordion>

            <FooterAccordion title="Transportation">
              <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/train`} className="block w-full">Train</Link></li>
              <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/bus`} className="block w-full">Bus</Link></li>
              <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/car`} className="block w-full">Rental Car</Link></li>
            </FooterAccordion>

            <FooterAccordion title="Learning Materials">
              <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#alerts`} className="block w-full">About Alerts</Link></li>
              <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#power-outages`} className="block w-full">Power outages</Link></li>
              <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#links`} className="block w-full">Links</Link></li>
            </FooterAccordion>
          </nav>
          
          <div className="mt-12 text-center text-sm opacity-80">
            ©2026 SafetyHokaido.
          </div>
        </div>

        {/* Desktop Layout */}
        <div className="hidden md:flex flex-col w-full">
          <div className="flex justify-between items-start w-full">
            
            {/* Logo */}
            <div className="w-[30%]">
              <Link href={`/${locale}`}>
                <Image src="/illustrations/logo_team.png" alt="SafetyHokaido" width={180} height={80} className="w-[180px] h-auto mt-4" />
              </Link>
            </div>
            
            {/* Links Columns */}
            <div className="flex-1 flex justify-center gap-16 lg:gap-24 pl-8">
              <div className="flex flex-col gap-4">
                <div className="mb-1">
                  <Link href={`/${locale}`} className="font-bold text-base hover:text-orange-300 hover:opacity-100 transition-all">Top</Link>
                </div>
                <FooterAccordion title="Disaster" defaultOpen={true}>
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/disaster/blizzard`} className="hover:underline block w-full">Blizzard</Link></li>
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/disaster/earthquake`} className="hover:underline block w-full">Earthquake</Link></li>
                </FooterAccordion>
              </div>

              <div className="flex flex-col">
                <FooterAccordion title="Transportation" defaultOpen={true} className="mt-[44px]">
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/train`} className="hover:underline block w-full">Train</Link></li>
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/bus`} className="hover:underline block w-full">Bus</Link></li>
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/car`} className="hover:underline block w-full">Rental Car</Link></li>
                </FooterAccordion>
              </div>

              <div className="flex flex-col">
                <FooterAccordion title="Learning Materials" defaultOpen={true} className="mt-[44px]">
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#alerts`} className="hover:underline block w-full">About Alerts</Link></li>
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#power-outages`} className="hover:underline block w-full">Power outages</Link></li>
                  <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#links`} className="hover:underline block w-full">Links</Link></li>
                </FooterAccordion>
              </div>
            </div>

            {/* Back to top Button */}
            <div className="w-[10%] flex justify-end">
              <button 
                onClick={scrollToTop}
                aria-label="Back to top"
                className="w-10 h-10 bg-orange-400 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-105 active:scale-95 mt-2"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m18 15-6-6-6 6"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div className="mt-16 text-center text-sm opacity-80">
            ©2026 SafetyHokkaido.
          </div>
        </div>

      </footer>
    </div>
  );
}
"""

with open('src/components/Footer.jsx', 'w') as out_f:
    out_f.write(new_footer)
