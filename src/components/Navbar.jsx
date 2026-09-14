'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <header className="fixed top-4 left-1/2 -translate-x-1/2 w-[90%] max-w-md bg-[#0047b3] text-white rounded-full px-6 py-3 flex justify-between items-center z-40 shadow-lg">
        <Link href="/" className="flex items-center">
          <Image src="/illustrations/logo_team.png" alt="TOPM TEAM" width={50} height={35} priority />
        </Link>
        <div className="flex items-center gap-4">
          <button aria-label="Language">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              <path d="M2 12h20"/>
            </svg>
          </button>
          <button aria-label="Menu" onClick={() => setIsOpen(true)}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="4" x2="20" y1="12" y2="12"/>
              <line x1="4" x2="20" y1="6" y2="6"/>
              <line x1="4" x2="20" y1="18" y2="18"/>
            </svg>
          </button>
        </div>
      </header>

      {/* Hamburger Menu Overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-[#0047b3] text-white z-50 p-8 overflow-y-auto w-full h-full">
          <div className="max-w-md mx-auto relative">
            <div className="flex justify-end gap-4 mb-10 mt-2">
              <button aria-label="Language">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                  <path d="M2 12h20"/>
                </svg>
              </button>
              <button onClick={() => setIsOpen(false)} aria-label="Close Menu">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            
            <div className="mb-8">
              <Link href="/" className="block" onClick={() => setIsOpen(false)}>
                <Image src="/illustrations/logo_team.png" alt="TOPM TEAM" width={90} height={45} />
              </Link>
            </div>
            
            <nav className="space-y-6 text-lg">
              <div>
                <Link href="/" onClick={() => setIsOpen(false)} className="font-bold">Top</Link>
              </div>
              
              <div>
                <h3 className="font-bold mb-3">Disaster</h3>
                <ul className="pl-4 space-y-3 opacity-90">
                  <li><Link href="/disaster/blizzard" onClick={() => setIsOpen(false)}>Blizzard</Link></li>
                  <li><Link href="/disaster/earthquake" onClick={() => setIsOpen(false)}>Earthquake</Link></li>
                </ul>
              </div>

              <div>
                <h3 className="font-bold mb-3">Transportation</h3>
                <ul className="pl-4 space-y-3 opacity-90">
                  <li><Link href="/transportation/train" onClick={() => setIsOpen(false)}>Train</Link></li>
                  <li><Link href="/transportation/bus" onClick={() => setIsOpen(false)}>Bus</Link></li>
                  <li><Link href="/transportation/car" onClick={() => setIsOpen(false)}>Rental Car</Link></li>
                </ul>
              </div>

              <div>
                <h3 className="font-bold mb-3">Learning Materials</h3>
                <ul className="pl-4 space-y-3 opacity-90">
                  <li><Link href="/learning-materials#alerts" onClick={() => setIsOpen(false)}>About Alerts</Link></li>
                  <li><Link href="/learning-materials#power-outages" onClick={() => setIsOpen(false)}>Power outages</Link></li>
                  <li><Link href="/learning-materials#links" onClick={() => setIsOpen(false)}>Links</Link></li>
                </ul>
              </div>
            </nav>
          </div>
        </div>
      )}
    </>
  );
}
