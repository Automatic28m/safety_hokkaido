import { Geist, Geist_Mono } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";
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
  src: "../fonts/Anuphan-VariableFont_wght.ttf",
  variable: "--font-anuphan",
});

const bowlby = localFont({
  src: "../fonts/BowlbyOneSC-Regular.ttf",
  variable: "--font-bowlby",
});

export const metadata = {
  title: "HOKGUIDEDO",
  description: "Hokkaido Disaster Guide for Tourist",
};

export default function RootLayout({ children }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${anuphan.variable} ${bowlby.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-gray-50">
        <Navbar />
        <main className="flex-1">
          {children}
        </main>
        <FloatingButtons />
        <Footer />
      </body>
    </html>
  );
}
