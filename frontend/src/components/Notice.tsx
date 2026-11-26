import { CircleAlert, CircleCheck, Info, TriangleAlert } from 'lucide-react'
import type { ReactNode } from 'react'

const ICONS = { info: Info, success: CircleCheck, error: CircleAlert, warning: TriangleAlert }

interface NoticeProps {
  tone?: keyof typeof ICONS
  role?: 'status' | 'alert'
  children: ReactNode
}

export function Notice({ tone = 'info', role, children }: NoticeProps) {
  const Icon = ICONS[tone]
  return (
    <div className={`notice notice-${tone}`} role={role}>
      <Icon size={18} aria-hidden="true" />
      <div>{children}</div>
    </div>
  )
}
