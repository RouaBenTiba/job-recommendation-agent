export function Spinner({ label = 'Chargement…' }: { label?: string }) {
  return (
    <div className="spinner" role="status">
      {label}
    </div>
  )
}
