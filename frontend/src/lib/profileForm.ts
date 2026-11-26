import type { EducationItem, ExperienceItem, Profile, ProfileUpdate } from '../api/types'
import type { ProfileFormValues } from './schemas'

const clean = (value: string) => value.trim()
const orNull = (value: string) => clean(value) || null
const yearOrNull = (value: string) => (clean(value) === '' ? null : Number(clean(value)))

export const emptyEducation = (): ProfileFormValues['education'][number] => ({
  school: '',
  degree: '',
  field_of_study: '',
  start_year: '',
  end_year: '',
})

export const emptyExperience = (): ProfileFormValues['experiences'][number] => ({
  company: '',
  title: '',
  start: '',
  end: '',
  description: '',
  technologies: [],
})

export function profileToForm(profile: Profile | null): ProfileFormValues {
  return {
    summary: profile?.summary ?? '',
    objectives: profile?.objectives ?? '',
    education: (profile?.education ?? []).map((item) => ({
      school: item.school,
      degree: item.degree ?? '',
      field_of_study: item.field_of_study ?? '',
      start_year: item.start_year === null ? '' : String(item.start_year),
      end_year: item.end_year === null ? '' : String(item.end_year),
    })),
    experiences: (profile?.experiences ?? []).map((item) => ({
      company: item.company,
      title: item.title,
      start: item.start ?? '',
      end: item.end ?? '',
      description: item.description ?? '',
      technologies: [...item.technologies],
    })),
    skills: [...(profile?.skills ?? [])],
    technologies: [...(profile?.technologies ?? [])],
    interests: [...(profile?.interests ?? [])],
  }
}

function normalize(values: ProfileFormValues): Required<ProfileUpdate> {
  const education: EducationItem[] = values.education.map((item) => ({
    school: clean(item.school),
    degree: orNull(item.degree),
    field_of_study: orNull(item.field_of_study),
    start_year: yearOrNull(item.start_year),
    end_year: yearOrNull(item.end_year),
  }))
  const experiences: ExperienceItem[] = values.experiences.map((item) => ({
    company: clean(item.company),
    title: clean(item.title),
    start: orNull(item.start),
    end: orNull(item.end),
    description: orNull(item.description),
    technologies: item.technologies.map(clean),
  }))
  return {
    summary: orNull(values.summary),
    objectives: orNull(values.objectives),
    education,
    experiences,
    skills: values.skills.map(clean),
    technologies: values.technologies.map(clean),
    interests: values.interests.map(clean),
  }
}

/**
 * The fields that really changed. Every PATCH creates a new profile version on the backend,
 * so only modified fields are sent, and nothing is sent when nothing changed.
 */
export function buildProfileUpdate(
  current: ProfileFormValues,
  initial: ProfileFormValues,
): ProfileUpdate {
  const now = normalize(current)
  const before = normalize(initial)
  const update: Record<string, unknown> = {}
  for (const key of Object.keys(now) as (keyof ProfileUpdate)[]) {
    if (JSON.stringify(now[key]) !== JSON.stringify(before[key])) update[key] = now[key]
  }
  return update as ProfileUpdate
}
