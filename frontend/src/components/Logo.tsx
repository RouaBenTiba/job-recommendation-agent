/** Logomark: a rising chevron over a saffron dot (a path that leads somewhere). */
export function Logo() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 32 32" width="32" height="32">
        <rect width="32" height="32" rx="9" fill="currentColor" />
        <path
          d="M9.5 19.5 16 10.5l6.5 9"
          fill="none"
          stroke="#ffffff"
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="16" cy="24" r="2.1" fill="#f0a32f" />
      </svg>
    </span>
  )
}
