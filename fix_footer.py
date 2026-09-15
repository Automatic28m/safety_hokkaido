import re

with open('src/components/Footer.jsx', 'r') as f:
    content = f.read()

new_footer = """'use client';

import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';

export default function Footer() {
  const pathname = usePathname();
  // Simple check for locale prefix to retain it in links
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
              className="w-10 h-10 bg-orange-400 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-105 shrink-0"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="m18 15-6-6-6 6"/>
              </svg>
            </button>
          </div>

          <nav className="space-y-6">
            <div>
              <Link href={`/${locale}`} className="font-bold text-lg">Top</Link>
            </div>
            
            <div>
              <h3 className="font-bold text-lg mb-2">Disaster</h3>
              <ul className="pl-6 space-y-2 opacity-90 text-[15px]">
                <li><Link href={`/${locale}/disaster/blizzard`}>Blizzard</Link></li>
                <li><Link href={`/${locale}/disaster/earthquake`}>Earthquake</Link></li>
              </ul>
            </div>

            <div>
              <h3 className="font-bold text-lg mb-2">Transportation</h3>
              <ul className="pl-6 space-y-2 opacity-90 text-[15px]">
                <li><Link href={`/${locale}/transportation/train`}>Train</Link></li>
                <li><Link href={`/${locale}/transportation/bus`}>Bus</Link></li>
                <li><Link href={`/${locale}/transportation/car`}>Rental Car</Link></li>
              </ul>
            </div>

            <div>
              <h3 className="font-bold text-lg mb-2">Learning Materials</h3>
              <ul className="pl-6 space-y-2 opacity-90 text-[15px]">
                <li><Link href={`/${locale}/learning-materials#alerts`}>About Alerts</Link></li>
                <li><Link href={`/${locale}/learning-materials#power-outages`}>Power outages</Link></li>
                <li><Link href={`/${locale}/learning-materials#links`}>Links</Link></li>
              </ul>
            </div>
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
              <div className="flex flex-col gap-6">
                <div>
                  <Link href={`/${locale}`} className="font-bold text-base hover:underline hover:opacity-100 transition-opacity">Top</Link>
                </div>
                <div>
                  <h3 className="font-bold text-base mb-3">Disaster</h3>
                  <ul className="pl-0 space-y-2 opacity-80 text-sm">
                    <li><Link href={`/${locale}/disaster/blizzard`} className="hover:underline">Blizzard</Link></li>
                    <li><Link href={`/${locale}/disaster/earthquake`} className="hover:underline">Earthquake</Link></li>
                  </ul>
                </div>
              </div>

              <div className="flex flex-col">
                <h3 className="font-bold text-base mb-3 mt-[44px]">Transportation</h3>
                <ul className="pl-0 space-y-2 opacity-80 text-sm">
                  <li><Link href={`/${locale}/transportation/train`} className="hover:underline">Train</Link></li>
                  <li><Link href={`/${locale}/transportation/bus`} className="hover:underline">Bus</Link></li>
                  <li><Link href={`/${locale}/transportation/car`} className="hover:underline">Rental Car</Link></li>
                </ul>
              </div>

              <div className="flex flex-col">
                <h3 className="font-bold text-base mb-3 mt-[44px]">Learning Materials</h3>
                <ul className="pl-0 space-y-2 opacity-80 text-sm">
                  <li><Link href={`/${locale}/learning-materials#alerts`} className="hover:underline">About Alerts</Link></li>
                  <li><Link href={`/${locale}/learning-materials#power-outages`} className="hover:underline">Power outages</Link></li>
                  <li><Link href={`/${locale}/learning-materials#links`} className="hover:underline">Links</Link></li>
                </ul>
              </div>
            </div>

            {/* Back to top Button */}
            <div className="w-[10%] flex justify-end">
              <button 
                onClick={scrollToTop}
                aria-label="Back to top"
                className="w-10 h-10 bg-orange-400 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-105 mt-2"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m18 15-6-6-6 6"/>
                </svg>
              </button>
            </div>
          </div>
          
          <div className="mt-16 text-center text-sm opacity-80">
            ©2026 SafetyHokaido.
          </div>
        </div>

      </footer>
    </div>
  );
}
"""

with open('src/components/Footer.jsx', 'w') as out_f:
    out_f.write(new_footer)
