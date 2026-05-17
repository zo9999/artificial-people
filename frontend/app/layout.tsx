import type { Metadata } from "next";
import type { ReactNode } from "react";
import { ClerkProvider } from "@clerk/nextjs";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

export const metadata: Metadata = {
  title: "Artificial People",
  description: "Create artificial people that act on the internet.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>
          <div className="app">
            <Sidebar />
            <main className="main">{children}</main>
          </div>
        </body>
      </html>
    </ClerkProvider>
  );
}
