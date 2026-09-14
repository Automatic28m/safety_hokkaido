import Link from "next/link";

export default function EmergencyContactPage() {
  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6] pt-24">
      <div className="w-[90%] max-w-md">
        
        {/* Header */}
        <h1 className="font-bowlby text-5xl font-black text-black tracking-tighter mb-2 leading-none uppercase">
          EMERGENCY<br/>CONTACT
        </h1>
        <div className="border-b-2 border-dashed border-gray-400 mb-8"></div>

        {/* Emergency Numbers */}
        <div className="space-y-4 mb-10">
          
          {/* Fire / ambulance */}
          <div className="bg-white rounded-3xl shadow-sm p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 shrink-0 flex justify-center items-center">
                <svg className="text-green-500 w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10 10h4"/><path d="M12 8v4"/><path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11h1v1a2 2 0 0 0 4 0v-1h8v1a2 2 0 0 0 4 0v-1h2a2 2 0 0 0 2-2V9.5C23 7.5 21 6 18.5 6H14"/></svg>
              </div>
              <div>
                <h2 className="text-gray-700 text-sm">Fire / ambulance</h2>
                <p className="text-5xl font-black text-black tracking-tighter">119</p>
              </div>
            </div>
            <div className="border-b-2 border-dashed border-gray-300 mb-4"></div>
            <p className="text-gray-700 text-sm leading-relaxed">
              Call for fires, serious injury, or sudden illness. Say which one you need.
            </p>
          </div>

          {/* Police */}
          <div className="bg-white rounded-3xl shadow-sm p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 shrink-0 flex justify-center items-center">
                <svg className="text-green-500 w-10 h-10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
              </div>
              <div>
                <h2 className="text-gray-700 text-sm">Police</h2>
                <p className="text-5xl font-black text-black tracking-tighter">110</p>
              </div>
            </div>
            <div className="border-b-2 border-dashed border-gray-300 mb-4"></div>
            <p className="text-gray-700 text-sm leading-relaxed">
              Call for crimes, accidents, theft, or when you feel in danger.
            </p>
          </div>

          {/* Coast guard */}
          <div className="bg-white rounded-3xl shadow-sm p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 shrink-0 flex justify-center items-center relative">
                {/* Custom Lifebuoy Icon */}
                <svg className="text-green-500 w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/>
                  <line x1="4.93" y1="4.93" x2="9.17" y2="9.17"/>
                  <line x1="14.83" y1="14.83" x2="19.07" y2="19.07"/>
                  <line x1="14.83" y1="9.17" x2="19.07" y2="4.93"/>
                  <line x1="14.83" y1="9.17" x2="18.36" y2="5.64"/>
                  <line x1="4.93" y1="19.07" x2="9.17" y2="14.83"/>
                </svg>
              </div>
              <div>
                <h2 className="text-gray-700 text-sm">Coast guard</h2>
                <p className="text-5xl font-black text-black tracking-tighter">118</p>
              </div>
            </div>
            <div className="border-b-2 border-dashed border-gray-300 mb-4"></div>
            <p className="text-gray-700 text-sm leading-relaxed">
              Call for accidents or trouble at sea, on the coast, or on boats.
            </p>
          </div>

        </div>

        {/* Links Header */}
        <h1 className="font-bowlby text-5xl font-black text-black tracking-tighter mb-2 leading-none uppercase mt-12">
          HELP DESK<br/>LINKS
        </h1>
        <div className="border-b-2 border-dashed border-gray-400 mb-8"></div>

        {/* Help Desk Links */}
        <div className="space-y-4 mb-10">
          
          <Link href="https://www.japan.travel/en/plan/hotline/" target="_blank" className="bg-white rounded-2xl p-6 shadow-sm flex items-center justify-between group hover:shadow-md transition-shadow">
            <div className="flex-1 pr-4">
              <div className="flex items-start gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 shrink-0 mt-1.5"></div>
                <h3 className="text-lg font-bold text-black leading-tight">Japan Visitor Hotline</h3>
              </div>
              <div className="border-t border-dashed border-gray-300 pt-2 mt-2">
                <p className="text-gray-600 text-sm">Japan Visitor Hotline (JNTO) — 24-hour support for travelers.</p>
              </div>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>

          <Link href="https://www.japan.travel/en/news/JapanSafeTravel/" target="_blank" className="bg-white rounded-2xl p-6 shadow-sm flex items-center justify-between group hover:shadow-md transition-shadow">
            <div className="flex-1 pr-4">
              <div className="flex items-start gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 shrink-0 mt-1.5"></div>
                <h3 className="text-lg font-bold text-black leading-tight">JNTO – Japan Safe Travel</h3>
              </div>
              <div className="border-t border-dashed border-gray-300 pt-2 mt-2">
                <p className="text-gray-600 text-sm">Disaster and safety information for travelers.</p>
              </div>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>

          <Link href="https://crisis.yahoo.co.jp/map/" target="_blank" className="bg-white rounded-2xl p-6 shadow-sm flex items-center justify-between group hover:shadow-md transition-shadow">
            <div className="flex-1 pr-4">
              <div className="flex items-start gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 shrink-0 mt-1.5"></div>
                <h3 className="text-lg font-bold text-black leading-tight">Evacuation Shelter Map</h3>
              </div>
              <div className="border-t border-dashed border-gray-300 pt-2 mt-2">
                <p className="text-gray-600 text-sm">Find the nearest evacuation shelter from your location.</p>
              </div>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>

          <Link href="#" target="_blank" className="bg-white rounded-2xl p-6 shadow-sm flex items-center justify-between group hover:shadow-md transition-shadow">
            <div className="flex-1 pr-4">
              <div className="flex items-start gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 shrink-0 mt-1.5"></div>
                <h3 className="text-lg font-bold text-black leading-tight">JMA – Weather Warnings</h3>
              </div>
              <div className="border-t border-dashed border-gray-300 pt-2 mt-2">
                <p className="text-gray-600 text-sm">Official weather warnings, including heavy snow, in multiple languages.</p>
              </div>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>

          <Link href="https://wwwtb.mlit.go.jp/hokkaido/unkoujouhou/index.html" target="_blank" className="bg-white rounded-2xl p-6 shadow-sm flex items-center justify-between group hover:shadow-md transition-shadow">
            <div className="flex-1 pr-4">
              <div className="flex items-start gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 shrink-0 mt-1.5"></div>
                <h3 className="text-lg font-bold text-black leading-tight">Hokkaido District Transport Bureau</h3>
              </div>
              <div className="border-t border-dashed border-gray-300 pt-2 mt-2">
                <p className="text-gray-600 text-sm">Public Transportation Service Updates in Hokkaido</p>
              </div>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>

          <Link href="https://www.jrhokkaido.co.jp/global/index.html" target="_blank" className="bg-white rounded-2xl p-6 shadow-sm flex items-center justify-between group hover:shadow-md transition-shadow">
            <div className="flex-1 pr-4">
              <div className="flex items-start gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 shrink-0 mt-1.5"></div>
                <h3 className="text-lg font-bold text-black leading-tight">HOKKAIDO RAILWAY COMPANY</h3>
              </div>
              <div className="border-t border-dashed border-gray-300 pt-2 mt-2">
                <p className="text-gray-600 text-sm">Check train times and delays on the official JR Hokkaido site.</p>
              </div>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>

          <Link href="https://www.jrhokkaidobus.com/en/" target="_blank" className="bg-white rounded-2xl p-6 shadow-sm flex items-center justify-between group hover:shadow-md transition-shadow">
            <div className="flex-1 pr-4">
              <div className="flex items-start gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 shrink-0 mt-1.5"></div>
                <h3 className="text-lg font-bold text-black leading-tight">JR Hokkaido Bus</h3>
              </div>
              <div className="border-t border-dashed border-gray-300 pt-2 mt-2">
                <p className="text-gray-600 text-sm">Check bus routes and times on the official JR Hokkaido Bus site.</p>
              </div>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform shadow-sm">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>

        </div>

      </div>
    </div>
  );
}
