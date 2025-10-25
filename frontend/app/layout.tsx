import type { Metadata } from "next";
import { Playfair_Display, Inter } from "next/font/google";
import "./globals.css";
import Script from "next/script";

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["900"],
  variable: "--font-playfair",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  weight: ["200", "300", "400", "500"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Haven - Patient Monitoring Platform",
  description: "Real-time patient monitoring and floor plan management for clinical trials",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${playfair.variable} ${inter.variable}`}>
      <body className={`${inter.className} font-inter antialiased bg-background text-neutral-950`}>
        {children}
      </body>
    </html>
  );
}
