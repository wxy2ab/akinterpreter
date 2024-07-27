import type { PropsWithChildren } from 'react'
import { Toaster } from "@/components/ui/toaster"
import { ThemeProvider } from "@/components/theme-provider"
import dynamic from 'next/dynamic'
import './globals.css' 

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body className="bg-background text-foreground">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
            <main className="flex h-screen overflow-hidden">
              {children}
            </main>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}