import type { PropsWithChildren } from 'react'
import { Toaster } from "@/components/ui/toaster"
import { ThemeProvider } from "@/components/theme-provider"
import dynamic from 'next/dynamic'
import './globals.css'  // 更新这一行

const ScrollManager = dynamic(() => import('@/components/ScrollManager'), { ssr: false })

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body className="bg-background text-foreground">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <ScrollManager>
            <main className="flex h-screen overflow-hidden">
              {children}
            </main>
          </ScrollManager>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}