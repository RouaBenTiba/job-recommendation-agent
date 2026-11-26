import type { ProfileFormValues } from '../lib/schemas'

interface ProfilePreviewProps {
  values: ProfileFormValues
  name: string
  version: number | null
}

const filled = (value: string) => value.trim() !== ''

function years(start: string, end: string): string {
  if (filled(start) && filled(end)) return `${start.trim()} – ${end.trim()}`
  if (filled(start)) return `Depuis ${start.trim()}`
  return filled(end) ? `Jusqu'en ${end.trim()}` : ''
}

function Chips({ items, empty }: { items: string[]; empty: string }) {
  if (items.length === 0) return <p className="sheet-empty">{empty}</p>
  return (
    <ul className="sheet-chips">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  )
}

/** The profile as a one-page CV, updated while the candidate types. */
export function ProfilePreview({ values, name, version }: ProfilePreviewProps) {
  const education = values.education.filter((item) => filled(item.school))
  const experiences = values.experiences.filter(
    (item) => filled(item.company) || filled(item.title),
  )

  return (
    <article className="sheet" aria-label="Aperçu du CV">
      <header className="sheet-header">
        <p className="sheet-name">{name}</p>
        <p className="sheet-meta">{version ? `Profil, version ${version}` : 'Nouveau profil'}</p>
      </header>

      <section className="sheet-block">
        <h3>Résumé</h3>
        {filled(values.summary) ? (
          <p>{values.summary}</p>
        ) : (
          <p className="sheet-empty">Votre résumé apparaîtra ici.</p>
        )}
      </section>

      {filled(values.objectives) && (
        <section className="sheet-block">
          <h3>Objectif</h3>
          <p>{values.objectives}</p>
        </section>
      )}

      <section className="sheet-block">
        <h3>Compétences</h3>
        <Chips items={values.skills} empty="Ajoutez vos compétences clés." />
      </section>

      <section className="sheet-block">
        <h3>Technologies</h3>
        <Chips items={values.technologies} empty="Ajoutez les outils que vous maîtrisez." />
      </section>

      <section className="sheet-block">
        <h3>Formation</h3>
        {education.length === 0 && <p className="sheet-empty">Vos diplômes apparaîtront ici.</p>}
        {education.map((item, index) => (
          <div key={index} className="sheet-entry">
            <strong>{item.school}</strong>
            {(filled(item.degree) || filled(item.field_of_study)) && (
              <span>{[item.degree, item.field_of_study].filter(filled).join(', ')}</span>
            )}
            {years(item.start_year, item.end_year) && (
              <span>{years(item.start_year, item.end_year)}</span>
            )}
          </div>
        ))}
      </section>

      <section className="sheet-block">
        <h3>Expériences</h3>
        {experiences.length === 0 && (
          <p className="sheet-empty">Vos stages et emplois apparaîtront ici.</p>
        )}
        {experiences.map((item, index) => (
          <div key={index} className="sheet-entry">
            <strong>{[item.title, item.company].filter(filled).join(', ')}</strong>
            {years(item.start, item.end) && <span>{years(item.start, item.end)}</span>}
            {filled(item.description) && <span>{item.description}</span>}
          </div>
        ))}
      </section>

      {values.interests.length > 0 && (
        <section className="sheet-block">
          <h3>Centres d&apos;intérêt</h3>
          <Chips items={values.interests} empty="" />
        </section>
      )}
    </article>
  )
}
