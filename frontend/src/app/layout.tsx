import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Wallbit — Growth challenge",
  description: "Experimento de pantalla de fondeo — Wallbit growth challenge",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body>
        <header className="site-header">
          <Link href="/" className="wordmark">
            Wall<span>bit</span>
          </Link>
        </header>
        <div className="site-content">{children}</div>
        <footer className="site-footer">
          Hecho por{" "}
          <a href="https://www.linkedin.com/in/imanol-urzaiz" target="_blank" rel="noopener noreferrer">
            Imanol Urzaiz
          </a>{" "}
          para el growth challenge de Wallbit.
        </footer>
      </body>
    </html>
  );
}
