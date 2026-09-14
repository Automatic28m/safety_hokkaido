'use client';

import Link from 'next/link';
import Image from 'next/image';

export default function Footer() {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <footer className="bg-[#0047b3] text-white p-8 pb-12 w-full">
      <div className="max-w-md mx-auto">
        <div className="flex justify-between items-start mb-8">
          <Link href="/">
            <Image src="/illustrations/logo_team.png" alt="TOPM TEAM" width={80} height={40} />
          </Link>
          <button 
            onClick={scrollToTop}
            aria-label="Back to top"
            className="w-10 h-10 bg-orange-400 rounded-full flex items-center justify-center shadow-lg transition-transform hover:scale-105"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="m18 15-6-6-6 6"/>
            </svg>
          </button>
        </div>

        <nav className="space-y-6">
          <div>
            <Link href="/" className="font-bold text-lg">Top</Link>
          </div>
          
          <div>
            <h3 className="font-bold text-lg mb-2">Disaster</h3>
            <ul className="pl-4 space-y-2 opacity-90">
              <li><Link href="/disaster/blizzard">Blizzard</Link></li>
              <li><Link href="/disaster/earthquake">Earthquake</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-2">Transportation</h3>
            <ul className="pl-4 space-y-2 opacity-90">
              <li><Link href="/transportation/train">Train</Link></li>
              <li><Link href="/transportation/bus">Bus</Link></li>
              <li><Link href="/transportation/car">Rental Car</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-2">Learning Materials</h3>
            <ul className="pl-4 space-y-2 opacity-90">
              <li><Link href="/learning/alerts">About Alerts</Link></li>
              <li><Link href="/learning/power-outages">Power outages</Link></li>
              <li><Link href="/learning/links">Links</Link></li>
            </ul>
          </div>
        </nav>

        <div className="mt-12 text-center text-sm opacity-80">
          ©2026 Hokguidedo.
        </div>
      </div>
    </footer>
  );
}
