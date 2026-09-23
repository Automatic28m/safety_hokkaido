import re

with open('src/app/[locale]/learning-materials/page.jsx', 'r') as f:
    content = f.read()

# Just append the other 4 links into the grid
extra_links = """
            <Link href="https://crisis.yahoo.co.jp/map/" target="_blank" rel="noopener noreferrer" className="flex flex-col md:flex-row md:items-center p-4 md:p-6 border-2 border-black md:border-none md:bg-white md:shadow-sm md:rounded-2xl hover:bg-gray-50 md:hover:shadow-md transition-all group md:justify-between">
              <div className="md:flex-1 md:pr-4">
                <div className="md:flex md:items-center md:gap-2 mb-1 md:mb-2">
                  <div className="hidden md:block w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
                  <span className="font-bold text-black text-lg md:text-xl">{t('link3Title')}</span>
                </div>
                <div className="hidden md:block border-t border-dashed border-gray-300 pt-2 mt-2">
                  <p className="text-gray-600 text-sm">Crisis mapping and information.</p>
                </div>
                <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2 md:hidden">https://crisis.yahoo.co.jp/map/</span>
              </div>
              <div className="hidden md:flex w-10 h-10 bg-orange-400 rounded-full justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </Link>
            
            <Link href="https://wwwtb.mlit.go.jp/hokkaido/unkoujouhou/index.html" target="_blank" rel="noopener noreferrer" className="flex flex-col md:flex-row md:items-center p-4 md:p-6 border-2 border-black md:border-none md:bg-white md:shadow-sm md:rounded-2xl hover:bg-gray-50 md:hover:shadow-md transition-all group md:justify-between">
              <div className="md:flex-1 md:pr-4">
                <div className="md:flex md:items-center md:gap-2 mb-1 md:mb-2">
                  <div className="hidden md:block w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
                  <span className="font-bold text-black text-lg md:text-xl">{t('link4Title')}</span>
                </div>
                <div className="hidden md:block border-t border-dashed border-gray-300 pt-2 mt-2">
                  <p className="text-gray-600 text-sm">Hokkaido transportation status.</p>
                </div>
                <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2 md:hidden">https://wwwtb.mlit.go.jp/hokkaido/unkoujouhou/index.html</span>
              </div>
              <div className="hidden md:flex w-10 h-10 bg-orange-400 rounded-full justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </Link>
            
            <Link href="https://www.jrhokkaido.co.jp/global/index.html" target="_blank" rel="noopener noreferrer" className="flex flex-col md:flex-row md:items-center p-4 md:p-6 border-2 border-black md:border-none md:bg-white md:shadow-sm md:rounded-2xl hover:bg-gray-50 md:hover:shadow-md transition-all group md:justify-between">
              <div className="md:flex-1 md:pr-4">
                <div className="md:flex md:items-center md:gap-2 mb-1 md:mb-2">
                  <div className="hidden md:block w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
                  <span className="font-bold text-black text-lg md:text-xl">{t('link5Title')}</span>
                </div>
                <div className="hidden md:block border-t border-dashed border-gray-300 pt-2 mt-2">
                  <p className="text-gray-600 text-sm">JR Hokkaido Railway Company.</p>
                </div>
                <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2 md:hidden">https://www.jrhokkaido.co.jp/global/index.html</span>
              </div>
              <div className="hidden md:flex w-10 h-10 bg-orange-400 rounded-full justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </Link>
            
            <Link href="https://www.jrhokkaidobus.com/en/" target="_blank" rel="noopener noreferrer" className="flex flex-col md:flex-row md:items-center p-4 md:p-6 border-2 border-black md:border-none md:bg-white md:shadow-sm md:rounded-2xl hover:bg-gray-50 md:hover:shadow-md transition-all group md:justify-between">
              <div className="md:flex-1 md:pr-4">
                <div className="md:flex md:items-center md:gap-2 mb-1 md:mb-2">
                  <div className="hidden md:block w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
                  <span className="font-bold text-black text-lg md:text-xl">{t('link6Title')}</span>
                </div>
                <div className="hidden md:block border-t border-dashed border-gray-300 pt-2 mt-2">
                  <p className="text-gray-600 text-sm">JR Hokkaido Bus Company.</p>
                </div>
                <span className="text-sm text-blue-600 break-all underline decoration-blue-300 underline-offset-2 md:hidden">https://www.jrhokkaidobus.com/en/</span>
              </div>
              <div className="hidden md:flex w-10 h-10 bg-orange-400 rounded-full justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </div>
            </Link>
          </div>
        </div>

      </div>
    </div>
  );
}
"""

content = content.replace("          </div>\n        </div>\n\n      </div>\n    </div>\n  );\n}", extra_links)

with open('src/app/[locale]/learning-materials/page.jsx', 'w') as f:
    f.write(content)
