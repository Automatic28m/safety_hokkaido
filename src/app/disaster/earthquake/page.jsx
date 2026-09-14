import Image from "next/image";
import Link from "next/link";

export default function EarthquakePage() {
  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6] pt-24">
      <div className="w-[90%] max-w-md">
        
        {/* Header */}
        <h1 className="font-bowlby text-5xl font-black text-black tracking-tighter mb-2">
          DISASTER
        </h1>
        <div className="border-b-2 border-dashed border-gray-400 mb-6"></div>

        {/* Tabs */}
        <div className="flex gap-0 mb-8">
          <Link href="/disaster/blizzard" className="bg-gray-300 text-gray-700 font-bold py-2 px-6 rounded-t-xl hover:bg-gray-400 transition-colors">
            Blizzard
          </Link>
          <div className="bg-orange-400 text-white font-bold py-2 px-6 rounded-t-xl">
            Earthquake
          </div>
        </div>

        {/* Content Box */}
        <div className="bg-white rounded-b-3xl rounded-tr-3xl shadow-md p-6 -mt-8 pt-8 mb-12 relative">
          <h2 className="font-bowlby text-4xl font-black text-black mb-4">EARTHQUAKE</h2>
          
          <div className="relative w-full aspect-[2/1] rounded-xl overflow-hidden mb-6 border-2 border-black">
            <Image 
              src="/illustrations/Earthquake .png" 
              alt="Earthquake Illustration" 
              fill 
              className="object-cover"
            />
          </div>

          <h3 className="text-2xl font-bold border-b-2 text-black border-black pb-1 inline-block mb-3">
            What is it?
          </h3>
          <p className="text-gray-800 leading-relaxed mb-6">
            Japan is one of the most <strong className="text-blue-700 font-bold">earthquake-prone</strong> countries in the world, so shaking can happen <strong className="text-blue-700 font-bold">at any time</strong>. It can make it hard to <strong className="text-blue-700 font-bold">stand or move safely</strong>.
          </p>

          <div className="space-y-4 mb-10">
            <div className="bg-green-500 rounded-full py-3 px-6 text-white font-bold text-lg shadow-md flex justify-between items-center cursor-pointer hover:bg-green-600 transition-colors">
              <span>What if it's happening now?</span>
            </div>
            <div className="bg-green-500 rounded-full py-3 px-6 text-white font-bold text-lg shadow-md flex justify-between items-center cursor-pointer hover:bg-green-600 transition-colors">
              <span>What can happen?</span>
            </div>
          </div>

          <h3 className="text-3xl font-black text-black tracking-tight mb-4">
            SHAKING LEVELS
          </h3>

          <div className="space-y-3 mb-12">
            <div className="border-2 border-black rounded-2xl p-3 flex justify-between items-center bg-white shadow-sm">
              <div>
                <h4 className="text-black font-bold text-lg">Shindo 1-2</h4>
                <p className="text-gray-600 text-sm">→ No action needed. Stay calm.</p>
              </div>
              <div className="bg-green-500 text-white font-bold text-xs py-2 px-4 rounded-xl text-center w-24">
                Slight<br/>Shaking
              </div>
            </div>

            <div className="border-2 border-black rounded-2xl p-3 flex justify-between items-center bg-white shadow-sm">
              <div>
                <h4 className="text-black font-bold text-lg">Shindo 3-4</h4>
                <p className="text-gray-600 text-sm">→ Get ready. Move from<br/>windows & shelves</p>
              </div>
              <div className="bg-orange-400 text-white font-bold text-xs py-2 px-4 rounded-xl text-center w-24">
                Clearly<br/>Felt
              </div>
            </div>

            <div className="border-2 border-black rounded-2xl p-3 flex justify-between items-center bg-white shadow-sm">
              <div>
                <h4 className="text-black font-bold text-lg">Shindo 5</h4>
                <p className="text-gray-600 text-sm">→ Drop, cover, hold on</p>
              </div>
              <div className="bg-red-500 text-white font-bold text-xs py-2 px-4 rounded-xl text-center w-24">
                Hard to<br/>walk<br/>Things fall
              </div>
            </div>

            <div className="border-2 border-black rounded-2xl p-3 flex justify-between items-center bg-white shadow-sm">
              <div>
                <h4 className="text-black font-bold text-lg">Shindo 6-7</h4>
                <p className="text-gray-600 text-sm">→ Protect your head,<br/>then evacuate</p>
              </div>
              <div className="bg-red-600 text-white font-bold text-xs py-2 px-4 rounded-xl text-center w-24">
                Can't<br/>Stand
              </div>
            </div>
          </div>

          {/* Tsunami Section embedded within Earthquake */}
          <div className="relative mt-8">
            <div className="absolute -left-6 top-[-30px] border-l-2 border-dashed border-gray-400 h-16"></div>
            <div className="absolute -left-6 top-0 bg-[#0047b3] text-white text-sm font-bold py-2 px-4 rounded-r-xl rounded-bl-xl shadow-md w-64">
              Near the coast? <br/>There's more you need to know.
              {/* Arrow pointing left */}
              <div className="absolute w-3 h-3 bg-[#0047b3] rotate-45 -left-1.5 top-3"></div>
            </div>
            
            <div className="pt-16">
              <h2 className="font-bowlby text-4xl font-black text-black mb-4">THUNAMI</h2>
              <div className="relative w-full aspect-[2/1] rounded-xl overflow-hidden mb-6 border-2 border-black">
                <Image 
                  src="/illustrations/Tsunami.png" 
                  alt="Tsunami Illustration" 
                  fill 
                  className="object-cover"
                />
              </div>

              <h3 className="text-2xl font-bold border-b-2 border-black pb-1 inline-block mb-3">
                What is it?
              </h3>
              <p className="text-gray-800 leading-relaxed mb-6">
                A <strong className="text-blue-700 font-bold">tsunami</strong> is a series of powerful waves caused by an earthquake under the sea. It can arrive <strong className="text-blue-700 font-bold">within minutes</strong>, so if you feel strong shaking near the coast, move to <strong className="text-blue-700 font-bold">high ground</strong> right away.
              </p>

              <div className="space-y-4 mb-4">
                <div className="bg-green-500 rounded-full py-3 px-6 text-white font-bold text-lg shadow-md text-center cursor-pointer hover:bg-green-600 transition-colors">
                  Where do I go?
                </div>
                <div className="bg-green-500 rounded-full py-3 px-6 text-white font-bold text-lg shadow-md text-center cursor-pointer hover:bg-green-600 transition-colors">
                  What can happen?
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Links Section */}
        <h2 className="font-bowlby text-5xl font-black text-black tracking-tighter mb-2 mt-12">LINKS</h2>
        <div className="border-b-2 border-dashed border-gray-400 mb-6"></div>

        <div className="space-y-4 mb-10">
          <Link href="/learning-materials" className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <h3 className="text-xl font-bold text-black">Evacuation Shelter Map</h3>
              </div>
              <p className="text-gray-600 text-sm border-t border-gray-200 pt-2 mt-2">Find the nearest evacuation shelter from your location.</p>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>
        </div>

      </div>
    </div>
  );
}
