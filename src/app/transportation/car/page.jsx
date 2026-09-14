import Image from "next/image";
import Link from "next/link";

export default function RentalCarPage() {
  return (
    <div className="flex flex-col items-center pb-10 bg-[#f4f7f6] pt-24">
      <div className="w-[90%] max-w-md">
        
        {/* Header */}
        <h1 className="font-bowlby text-5xl font-black text-black tracking-tighter mb-2 leading-none uppercase">
          TRANS<br/>PORTATION
        </h1>
        <div className="border-b-2 border-dashed border-gray-400 mb-6"></div>

        {/* Tabs */}
        <div className="flex gap-0 mb-8">
          <Link href="/transportation/train" className="bg-gray-300 text-gray-700 font-bold py-2 px-6 rounded-t-xl hover:bg-gray-400 transition-colors flex-1 text-center">
            Train
          </Link>
          <Link href="/transportation/bus" className="bg-gray-300 text-gray-700 font-bold py-2 px-6 rounded-t-xl hover:bg-gray-400 transition-colors flex-1 text-center">
            Bus
          </Link>
          <div className="bg-orange-400 text-white font-bold py-2 px-4 rounded-t-xl z-10 flex-1 text-center whitespace-nowrap">
            Rental Car
          </div>
        </div>

        {/* Content Box */}
        <div className="bg-white rounded-b-3xl shadow-md p-6 -mt-8 pt-8 mb-12">
          <h2 className="font-bowlby text-4xl font-black text-black mb-4 uppercase">RENTAL CAR</h2>
          
          <div className="relative w-full aspect-[2/1] rounded-xl overflow-hidden mb-6 border-2 border-black bg-green-500">
            <Image 
              src="/illustrations/car.png" 
              alt="Car Illustration" 
              fill 
              className="object-contain p-2"
            />
          </div>

          <div className="relative mb-6">
            <div className="inline-block bg-[#0047b3] text-white font-bold py-1.5 px-4 rounded-md text-lg">
              How to ride
            </div>
            {/* Tooltip triangle */}
            <div className="absolute w-3 h-3 bg-[#0047b3] rotate-45 left-6 -bottom-1"></div>
          </div>

          {/* Timeline Steps */}
          <div className="relative pl-8 space-y-8 mt-8">
            {/* Vertical dashed line */}
            <div className="absolute left-[38px] top-6 bottom-6 w-px border-l-2 border-dashed border-gray-300"></div>

            {/* Step 1 */}
            <div className="relative">
              <div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">
                <Image src="/icons/license.svg" width={24} height={24} alt="icon" />
              </div>
              <h3 className="text-blue-700 font-bold text-sm tracking-widest mb-0.5">STEP1</h3>
              <h4 className="text-xl font-bold text-black border-b border-gray-300 pb-1 mb-2 inline-block w-full">Bring the right license</h4>
              <p className="text-gray-700 text-sm">
                You cannot drive in Japan with only your home country's license. You need an International Driving Permit (IDP) based on the 1949 Geneva Convention, or an official Japanese translation for some countries.
              </p>
            </div>

            {/* Step 2 */}
            <div className="relative">
              <div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">
                <Image src="/icons/circle-key.svg" width={24} height={24} alt="icon" />
              </div>
              <h3 className="text-blue-700 font-bold text-sm tracking-widest mb-0.5">STEP2</h3>
              <h4 className="text-xl font-bold text-black border-b border-gray-300 pb-1 mb-2 inline-block w-full">Book & pick up</h4>
              <p className="text-gray-700 text-sm">
                At the rental counter, show your IDP, home license, and passport. Staff will check the car with you and explain the return rules.
              </p>
            </div>

            {/* Step 3 */}
            <div className="relative">
              <div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">
                <Image src="/icons/steering-wheel.svg" width={24} height={24} alt="icon" />
              </div>
              <h3 className="text-blue-700 font-bold text-sm tracking-widest mb-0.5">STEP3</h3>
              <h4 className="text-xl font-bold text-black border-b border-gray-300 pb-1 mb-2 inline-block w-full">Know the basic rules</h4>
              <p className="text-gray-700 text-sm">
                In Japan, drive on the left side of the road. Come to a full stop at every stop sign (a red triangle). Everyone must wear a seatbelt, and using a phone while driving is banned.
              </p>
            </div>

            {/* Step 4 */}
            <div className="relative">
              <div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">
                <Image src="/icons/gas-station.svg" width={24} height={24} alt="icon" />
              </div>
              <h3 className="text-blue-700 font-bold text-sm tracking-widest mb-0.5">STEP4</h3>
              <h4 className="text-xl font-bold text-black border-b border-gray-300 pb-1 mb-2 inline-block w-full">Refuel & park</h4>
              <p className="text-gray-700 text-sm">
                Fill up before returning the car, and keep the receipt — most rentals require a full tank on return. Park only in marked parking lots or metered spaces.
              </p>
            </div>
            
            {/* Step 5 */}
            <div className="relative">
              <div className="absolute -left-12 bg-white border-2 border-black rounded-full w-12 h-12 flex justify-center items-center z-10">
                <Image src="/icons/car.svg" width={24} height={24} alt="icon" />
              </div>
              <h3 className="text-blue-700 font-bold text-sm tracking-widest mb-0.5">STEP5</h3>
              <h4 className="text-xl font-bold text-black border-b border-gray-300 pb-1 mb-2 inline-block w-full">Return the car</h4>
              <p className="text-gray-700 text-sm">
                Return the car to the agreed place by the agreed time, with a full tank. Staff will check the car and fuel. If you'll be late, call the rental company as early as possible.
              </p>
            </div>
          </div>
        </div>

        {/* Links Section */}
        <h2 className="font-bowlby text-5xl font-black text-black tracking-tighter mb-2">LINKS</h2>
        <div className="border-b-2 border-dashed border-gray-400 mb-6"></div>

        <div className="space-y-4 mb-10">
          <Link href="/learning-materials" className="bg-white rounded-2xl p-6 shadow-md flex items-center justify-between group hover:shadow-lg transition-shadow">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 shrink-0"></div>
                <h3 className="text-lg font-bold text-black leading-tight">Hokkaido District Transport Bureau</h3>
              </div>
              <p className="text-gray-600 text-sm border-t border-gray-200 pt-2 mt-2">Public Transportation Service Updates in Hokkaido</p>
            </div>
            <div className="w-10 h-10 bg-orange-400 rounded-full flex justify-center items-center text-white shrink-0 group-hover:scale-110 transition-transform ml-2">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m9 18 6-6-6-6"/></svg>
            </div>
          </Link>
        </div>

      </div>
    </div>
  );
}
