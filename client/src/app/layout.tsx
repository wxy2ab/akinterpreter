import type { PropsWithChildren } from 'react'
import { Toaster } from "@/components/ui/toaster"
import { ThemeProvider } from "@/components/theme-provider"
import dynamic from 'next/dynamic'

const ScrollManager = dynamic(() => import('@/components/ScrollManager'), { ssr: false })

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="dark">
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <ScrollManager>
            <div className="h-screen w-screen overflow-hidden">
              {children}
            </div>
          </ScrollManager>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}