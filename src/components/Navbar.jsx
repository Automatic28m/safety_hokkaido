'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);
  const t = useTranslations('Navbar');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const toggleLanguage = () => {
    const nextLocale = locale === 'en' ? 'th' : 'en';
    // Replace the leading locale in the path, e.g. /en/about -> /th/about
    let newPath = pathname.replace(new RegExp(`^\\/${locale}`), `/${nextLocale}`);
    if (newPath === pathname) newPath = `/${nextLocale}${pathname}`; // fallback
    router.push(newPath);
  };

  return (
    <>
      <header className="fixed top-4 left-1/2 -translate-x-1/2 w-[90%] max-w-md bg-[#0047b3] text-white rounded-full px-6 py-3 flex justify-between items-center z-40 shadow-lg">
        <Link href={`/${locale}`} className="flex items-center">
          <Image src="/illustrations/logo_team.png" alt="TOPM TEAM" width={50} height={35} priority />
        </Link>
        <div className="flex items-center gap-4">
          <button onClick={toggleLanguage} aria-label="Language" className="flex items-center gap-1 font-bold text-sm bg-white/20 px-2 py-1 rounded-lg hover:bg-white/30 transition-colors">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              <path d="M2 12h20"/>
            </svg>
            {locale.toUpperCase()}
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
              <button onClick={toggleLanguage} aria-label="Language" className="flex items-center gap-1 font-bold text-lg bg-white/20 px-3 py-1 rounded-lg hover:bg-white/30 transition-colors">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                  <path d="M2 12h20"/>
                </svg>
                {locale.toUpperCase()}
              </button>
              <button onClick={() => setIsOpen(false)} aria-label="Close Menu">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            </div>
            
            <div className="mb-8">
              <Link href={`/${locale}`} className="block" onClick={() => setIsOpen(false)}>
                <Image src="/illustrations/logo_team.png" alt="TOPM TEAM" width={90} height={45} />
              </Link>
            </div>
            
            <nav className="space-y-6 text-lg">
              <div>
                <Link href={`/${locale}`} onClick={() => setIsOpen(false)} className="font-bold">Top</Link>
              </div>
              
              <div>
                <h3 className="font-bold mb-3">{t('disaster')}</h3>
                <ul className="pl-4 space-y-3 opacity-90">
                  <li><Link href={`/${locale}/disaster/blizzard`} onClick={() => setIsOpen(false)}>{t('blizzard')}</Link></li>
                  <li><Link href={`/${locale}/disaster/earthquake`} onClick={() => setIsOpen(false)}>{t('earthquake')}</Link></li>
                </ul>
              </div>

              <div>
                <h3 className="font-bold mb-3">{t('transportation')}</h3>
                <ul className="pl-4 space-y-3 opacity-90">
                  <li><Link href={`/${locale}/transportation/train`} onClick={() => setIsOpen(false)}>{t('train')}</Link></li>
                  <li><Link href={`/${locale}/transportation/bus`} onClick={() => setIsOpen(false)}>{t('bus')}</Link></li>
                  <li><Link href={`/${locale}/transportation/car`} onClick={() => setIsOpen(false)}>{t('car')}</Link></li>
                </ul>
              </div>

              <div>
                <h3 className="font-bold mb-3">{t('learningMaterials')}</h3>
                <ul className="pl-4 space-y-3 opacity-90">
                  <li><Link href={`/${locale}/learning-materials#alerts`} onClick={() => setIsOpen(false)}>{t('alerts')}</Link></li>
                  <li><Link href={`/${locale}/learning-materials#power-outages`} onClick={() => setIsOpen(false)}>{t('powerOutages')}</Link></li>
                  <li><Link href={`/${locale}/learning-materials#links`} onClick={() => setIsOpen(false)}>{t('helpDesk')}</Link></li>
                </ul>
              </div>
            </nav>
          </div>
        </div>
      )}
    </>
  );
}
