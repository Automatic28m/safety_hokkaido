import re

with open('src/components/Navbar.jsx', 'r') as f:
    content = f.read()

# 1. Update backgrounds
content = content.replace('bg-[#0047b3]', 'bg-gradient-to-r from-[#0047b3] to-[#0c8a9e]')
content = content.replace('bg-gradient-to-r from-[#0047b3] to-[#0c8a9e] text-white z-50', 'bg-gradient-to-b from-[#0047b3] to-[#0c8a9e] text-white z-50')

# 2. Inject NavAccordion component
accordion_code = """
const NavAccordion = ({ title, children, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="mb-4">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex justify-between items-center font-bold text-xl mb-3 hover:text-orange-300 transition-colors focus:outline-none group pr-2"
      >
        <span className="text-left">{title}</span>
        <svg 
          className={`w-6 h-6 transform transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} 
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      <div 
        className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[300px] opacity-100' : 'max-h-0 opacity-0'}`}
      >
        <ul className="pl-4 space-y-4 opacity-90 text-lg pb-4">
          {children}
        </ul>
      </div>
    </div>
  );
};

export default function Navbar() {
"""
content = content.replace('export default function Navbar() {', accordion_code)


# 3. Replace the Mobile Menu Links with NavAccordions
mobile_nav = """            <nav className="space-y-2 text-lg">
              <div className="mb-6">
                <Link href={`/${locale}`} onClick={() => setIsOpen(false)} className="font-bold text-xl hover:text-orange-300 transition-colors">Top</Link>
              </div>

              <NavAccordion title={t('disaster')}>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/disaster/blizzard`} onClick={() => setIsOpen(false)} className="block w-full">{t('blizzard')}</Link></li>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/disaster/earthquake`} onClick={() => setIsOpen(false)} className="block w-full">{t('earthquake')}</Link></li>
              </NavAccordion>

              <NavAccordion title={t('transportation')}>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/train`} onClick={() => setIsOpen(false)} className="block w-full">{t('train')}</Link></li>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/bus`} onClick={() => setIsOpen(false)} className="block w-full">{t('bus')}</Link></li>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/transportation/car`} onClick={() => setIsOpen(false)} className="block w-full">{t('car')}</Link></li>
              </NavAccordion>

              <NavAccordion title={t('learningMaterials')}>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#alerts`} onClick={() => setIsOpen(false)} className="block w-full">{t('alerts')}</Link></li>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#power-outages`} onClick={() => setIsOpen(false)} className="block w-full">{t('powerOutages')}</Link></li>
                <li className="transition-transform hover:translate-x-2"><Link href={`/${locale}/learning-materials#links`} onClick={() => setIsOpen(false)} className="block w-full">{t('helpDesk')}</Link></li>
              </NavAccordion>
            </nav>"""

content = re.sub(r'<nav className="space-y-6 text-lg">.*?</nav>', mobile_nav, content, flags=re.DOTALL)


with open('src/components/Navbar.jsx', 'w') as out_f:
    out_f.write(content)
