import { describe, expect, it } from 'vitest'
import { PROFILE } from '../test/mockApi'
import type { Profile } from '../api/types'
import { buildProfileUpdate, profileToForm } from './profileForm'

const profile = PROFILE as Profile

describe('profileToForm', () => {
  it('turns nulls into empty strings and years into text', () => {
    const form = profileToForm(profile)
    expect(form.objectives).toBe('')
    expect(form.education[0]).toMatchObject({
      school: 'ENIT',
      field_of_study: '',
      start_year: '2023',
      end_year: '2026',
    })
    expect(form.experiences[0]).toMatchObject({ end: '', description: '' })
  })

  it('gives an empty form when there is no profile yet', () => {
    expect(profileToForm(null)).toEqual({
      summary: '',
      objectives: '',
      education: [],
      experiences: [],
      skills: [],
      technologies: [],
      interests: [],
    })
  })
})

describe('buildProfileUpdate', () => {
  it('sends nothing when nothing changed (each PATCH would create a version)', () => {
    const initial = profileToForm(profile)
    expect(buildProfileUpdate(structuredClone(initial), initial)).toEqual({})
  })

  it('ignores whitespace-only changes', () => {
    const initial = profileToForm(profile)
    const edited = {
      ...structuredClone(initial),
      summary: `  ${initial.summary}  `,
      skills: [' Travail en équipe '],
    }
    expect(buildProfileUpdate(edited, initial)).toEqual({})
  })

  it('sends only the fields that changed', () => {
    const initial = profileToForm(profile)
    const edited = { ...structuredClone(initial), skills: [...initial.skills, 'Rigueur'] }
    expect(buildProfileUpdate(edited, initial)).toEqual({
      skills: ['Travail en équipe', 'Rigueur'],
    })
  })

  it('converts the form back to the API format (nulls, numbers)', () => {
    const initial = profileToForm(null)
    const edited = {
      ...initial,
      summary: '  ',
      education: [
        {
          school: ' ENIT ',
          degree: '',
          field_of_study: ' Informatique',
          start_year: '2023',
          end_year: '',
        },
      ],
    }
    expect(buildProfileUpdate(edited, initial)).toEqual({
      education: [
        {
          school: 'ENIT',
          degree: null,
          field_of_study: 'Informatique',
          start_year: 2023,
          end_year: null,
        },
      ],
    })
  })

  it('can clear a text field with null', () => {
    const initial = profileToForm(profile)
    expect(buildProfileUpdate({ ...structuredClone(initial), summary: '' }, initial)).toEqual({
      summary: null,
    })
  })
})
