import re

with open('src/components/Navbar.jsx', 'r') as f:
    content = f.read()

# I will replace the return block for the <header> part.

header_old_regex = r"<header className=.*?<\/header>"
# Actually I'll replace everything inside the return up to the hamburger menu overlay

start_idx = content.find('  return (\n    <>\n') + 17
end_idx = content.find('      {/* Hamburger Menu Overlay */}')

new_header = """
      <header className="fixed top-4 left-1/2 -translate-x-1/2 w-[90%] max-w-md md:max-w-5xl lg:max-w-[1200px] bg-[#0047b3] text-white rounded-full px-6 md:px-10 py-3 md:py-3 flex justify-between items-center z-40 shadow-lg">
        
        {/* Left Section: Logo + Desktop Lang Switcher */}
        <div className="flex items-center gap-2 md:gap-10">
          <Link href={`/${locale}`} className="flex items-center">
            <Image src="/illustrations/logo_team.png" alt="SafetyHokaido" width={50} height={35} priority className="w-[50px] md:w-[70px] h-auto" />
          </Link>
          
          {/* Desktop Lang Switcher (Hidden on mobile) */}
          <button onClick={toggleLanguage} aria-label="Language" className="hidden md:flex relative items-center justify-center w-10 h-10 hover:opacity-80 transition-opacity mt-1">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
              <path d="M2 12h20"/>
            </svg>
            <div className="absolute -top-1 -right-2 bg-white text-[#0047b3] font-bold text-[9px] w-5 h-5 rounded-full flex items-center justify-center shadow-sm">
              {locale.toUpperCase()}
            </div>
          </button>
        </div>

        {/* Right Section: Desktop Links OR Mobile Menu Controls */}
        <div className="flex items-center">
          
          {/* Desktop Links (Hidden on mobile) */}
          <nav className="hidden md:flex items-center gap-8 lg:gap-12 font-medium text-sm lg:text-base uppercase tracking-wider">
             <Link href={`/${locale}`} className="hover:opacity-70 transition-opacity">Home</Link>
             <Link href={`/${locale}/disaster/earthquake`} className="hover:opacity-70 transition-opacity">{t('disaster')}</Link>
             <Link href={`/${locale}/transportation/train`} className="hover:opacity-70 transition-opacity">{t('transportation')}s</Link>
             <Link href={`/${locale}/learning-materials`} className="hover:opacity-70 transition-opacity">{t('learningMaterials')}</Link>
          </nav>

          {/* Mobile Lang Switcher + Hamburger (Hidden on desktop) */}
          <div className="flex md:hidden items-center gap-4">
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
        </div>
      </header>\n\n"""

new_content = content[:start_idx] + new_header + content[end_idx:]

with open('src/components/Navbar.jsx', 'w') as f:
    f.write(new_content)
