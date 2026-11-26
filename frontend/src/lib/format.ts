const dateTime = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })

export const formatDateTime = (iso: string) => dateTime.format(new Date(iso))

export const SOURCE_LABELS: Record<string, string> = {
  llm: "Extrait par l'IA",
  manual: 'Saisi manuellement',
}

export const sourceLabel = (source: string) => SOURCE_LABELS[source] ?? source
