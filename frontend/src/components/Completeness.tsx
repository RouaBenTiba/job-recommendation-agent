export interface CompletenessSection {
  label: string
  done: boolean
}

/** How much of the profile is filled in: five segments, one per section the recommender reads. */
export function Completeness({ sections }: { sections: CompletenessSection[] }) {
  const done = sections.filter((section) => section.done).length
  const missing = sections.filter((section) => !section.done).map((section) => section.label)

  return (
    <div className="completeness">
      <div
        className="meter"
        role="img"
        aria-label={`${done} sections sur ${sections.length} renseignées`}
      >
        {sections.map((section, index) => (
          <span
            key={section.label}
            className={section.done ? 'meter-seg is-done' : 'meter-seg'}
            style={{ '--i': index } as React.CSSProperties}
          />
        ))}
      </div>
      <p className="completeness-text">
        <strong>
          {done} sur {sections.length}
        </strong>{' '}
        sections renseignées.{' '}
        {missing.length > 0 ? `À compléter : ${missing.join(', ')}.` : 'Votre profil est complet.'}
      </p>
    </div>
  )
}
