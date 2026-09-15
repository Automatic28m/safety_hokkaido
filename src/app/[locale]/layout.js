import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import { notFound } from 'next/navigation';
import { Geist, Geist_Mono } from "next/font/google";
import localFont from "next/font/local";
import "../globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import FloatingButtons from "@/components/FloatingButtons";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const anuphan = localFont({
  src: "../../fonts/Anuphan-VariableFont_wght.ttf",
  variable: "--font-anuphan",
});

const torsilp = localFont({
  src: "../../fonts/TorsilpTontula.ttf",
  variable: "--font-torsilp",
});

export const metadata = {
  title: "SafetyHokaido",
  description: "Hokkaido Disaster Guide for Tourist",
};

export default async function RootLayout({ children, params }) {
  const { locale } = await params;
  
  if (!['en', 'th'].includes(locale)) {
    notFound();
  }
  
  const messages = await getMessages();

  return (
    <html
      lang={locale}
      className={`${geistSans.variable} ${geistMono.variable} ${anuphan.variable} ${torsilp.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#f4f7f6]">
        <NextIntlClientProvider messages={messages}>
          <Navbar />
          <main className="flex-1">
            {children}
          </main>
          <FloatingButtons />
          <Footer />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
