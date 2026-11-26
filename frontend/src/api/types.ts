export const CONTRACT_TYPES = [
  'internship',
  'apprenticeship',
  'full_time',
  'part_time',
  'contract',
] as const
export type ContractType = (typeof CONTRACT_TYPES)[number]

export const CONTRACT_LABELS: Record<ContractType, string> = {
  internship: 'Stage',
  apprenticeship: 'Alternance',
  full_time: 'Temps plein (CDI)',
  part_time: 'Temps partiel',
  contract: 'Contrat (CDD, freelance)',
}

export interface User {
  id: string
  email: string
  full_name: string | null
  created_at: string
}

export interface EducationItem {
  school: string
  degree: string | null
  field_of_study: string | null
  start_year: number | null
  end_year: number | null
}

export interface ExperienceItem {
  company: string
  title: string
  start: string | null
  end: string | null
  description: string | null
  technologies: string[]
}

export interface Profile {
  id: string
  version: number
  is_current: boolean
  cv_id: string | null
  source: string
  extraction_model: string | null
  summary: string | null
  objectives: string | null
  education: EducationItem[]
  experiences: ExperienceItem[]
  skills: string[]
  technologies: string[]
  interests: string[]
  created_at: string
  updated_at: string
}

export interface ProfileVersion {
  id: string
  version: number
  is_current: boolean
  source: string
  extraction_model: string | null
  created_at: string
}

/** Partial update: only the keys that are sent are changed. */
export type ProfileUpdate = Partial<
  Pick<
    Profile,
    'summary' | 'objectives' | 'education' | 'experiences' | 'skills' | 'technologies' | 'interests'
  >
>

export interface Preferences {
  id: string | null
  contract_types: string[]
  locations: string[]
  domains: string[]
  remote_ok: boolean
  willing_to_relocate: boolean
  updated_at: string | null
}

/** Full replacement. */
export type PreferencesUpdate = Omit<Preferences, 'id' | 'updated_at'>

export interface Cv {
  id: string
  filename: string
  content_type: string
  file_size_bytes: number
  status: string
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface CvExtraction {
  cv_id: string
  status: string
  method: string
  page_count: number
  pages_read: number
  truncated: boolean
  characters: number
  text: string
}
