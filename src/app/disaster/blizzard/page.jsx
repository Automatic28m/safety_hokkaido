import Image from "next/image";
import Link from "next/link";

export default function BlizzardPage() {
  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6] pt-24">
      <div className="w-[90%] max-w-md">
        
        {/* Header */}
        <h1 className="font-torsilp text-5xl font-black text-black tracking-wider mb-2">
          DISASTER
        </h1>
        <div className="border-b-2 border-dashed border-gray-400 mb-6"></div>

        {/* Tabs */}
        <div className="flex gap-0 mb-8">
          <div className="bg-orange-400 text-white font-bold py-2 px-6 rounded-t-xl">
            Blizzard
          </div>
          <Link href="/disaster/earthquake" className="bg-gray-300 text-gray-700 font-bold py-2 px-6 rounded-t-xl hover:bg-gray-400 transition-colors">
            Earthquake
          </Link>
        </div>

        {/* Content Box */}
        <div className="bg-white rounded-b-3xl rounded-tr-3xl shadow-md p-6 -mt-8 pt-8 mb-12">
          <h2 className="font-torsilp text-4xl font-black text-black mb-4">BLIZZARD</h2>
          
          <div className="relative w-full aspect-[2/1] rounded-xl overflow-hidden mb-6 border-2 border-black">
            <Image 
              src="/illustrations/Blizzard.png" 
              alt="Blizzard Illustration" 
              fill 
              className="object-cover"
            />
          </div>

          <h3 className="text-black text-2xl font-bold border-b-2 border-black pb-1 inline-block mb-3">
            What is it?
          </h3>
          <p className="text-gray-800 leading-relaxed mb-6">
            A <strong className="text-blue-700 font-bold">blizzard</strong> is a severe snowstorm with <strong className="text-blue-700 font-bold">strong winds</strong>. The wind blows snow through the air, making it <strong className="text-blue-700 font-bold">difficult to see and travel safely</strong>.
          </p>

          <div className="space-y-4 mb-8">
            {/* Expanded Green Button */}
            <div className="bg-green-500 rounded-2xl p-4 text-white shadow-md">
              <div className="flex justify-between items-center font-bold text-lg mb-2 cursor-pointer">
                <span>What if it's happening now?</span>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m18 15-6-6-6 6"/></svg>
              </div>
              <p className="text-sm opacity-90">What if it's happening now?</p>
            </div>
            
            {/* Regular Green Button */}
            <div className="bg-green-500 rounded-full py-3 px-6 text-white font-bold text-lg shadow-md flex justify-between items-center cursor-pointer hover:bg-green-600 transition-colors">
              <span>What can happen?</span>
            </div>
          </div>

          <h3 className="text-2xl font-bold border-b-2 border-black pb-1 inline-block mb-6 text-black">
            What's your situation?
          </h3>

          <div className="space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <svg className="text-green-500 w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                <h4 className="text-xl font-bold text-green-500">Hotel or Room</h4>
              </div>
              <p className="text-gray-700">Do not go outside while a heavy snow or blizzard warning is in effect. Change or delay your plans. Check the weather forecast and transport status before you leave.</p>
            </div>

            <div className="pl-4 border-l-2 border-gray-200 relative">
              <div className="absolute w-3 h-3 bg-green-500 rounded-full -left-[7px] top-1.5"></div>
              <h5 className="text-lg font-bold text-gray-800 mb-1">If you still want to go out in heavy snow</h5>
              <p className="text-gray-700 text-sm">Wear warm layers, and cover your skin with a hat, gloves, and scarf. Stay close by and avoid going far.</p>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-2 mt-6">
                <svg className="text-green-500 w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3"/></svg>
                <h4 className="text-xl font-bold text-green-500">If you're outside</h4>
              </div>
              <p className="text-gray-700">Check train and bus status before you head back — delays and cancellations are common in heavy snow. The subway is the most reliable option, as it runs underground and is less affected by snow.</p>
            </div>

            <div className="pl-4 border-l-2 border-gray-200 relative">
              <div className="absolute w-3 h-3 bg-green-500 rounded-full -left-[7px] top-1.5"></div>
              <h5 className="text-lg font-bold text-gray-800 mb-1">If you can't get back</h5>
              <p className="text-gray-700 text-sm">Don't force your way through a blizzard. Find a warm place to stay and wait it out. If you can't return to your hotel, contact them, and look for a nearby hotel if needed.</p>
            </div>
          </div>
        </div>

        {/* Links Section */}
        <h2 className="font-torsilp text-5xl font-black text-black tracking-wider mb-2">LINKS</h2>
        <div className="border-b-2 border-dashed border-gray-400 mb-6"></div>

        <div className="space-y-4">
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

          <Link href="/learning-materials" className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <h3 className="text-xl font-bold text-black">JMA – Weather Warnings</h3>
              </div>
              <p className="text-gray-600 text-sm border-t border-gray-200 pt-2 mt-2">Official weather warnings, including heavy snow, in multiple languages.</p>
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
