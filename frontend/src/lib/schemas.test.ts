import { describe, expect, it } from 'vitest'
import { emptyEducation, emptyExperience } from './profileForm'
import { loginSchema, preferencesFormSchema, profileFormSchema, registerSchema } from './schemas'

const messages = (result: { success: boolean; error?: { issues: { message: string }[] } }) =>
  result.error?.issues.map((issue) => issue.message) ?? []

const profile = (overrides: object = {}) => ({
  summary: '',
  objectives: '',
  education: [],
  experiences: [],
  skills: [],
  technologies: [],
  interests: [],
  ...overrides,
})

describe('loginSchema', () => {
  it('requires an email and a password', () => {
    expect(messages(loginSchema.safeParse({ email: '', password: '' }))).toEqual([
      "L'adresse e-mail est obligatoire",
      'Le mot de passe est obligatoire',
    ])
  })

  it('rejects an invalid email and trims a valid one', () => {
    expect(messages(loginSchema.safeParse({ email: 'nope', password: 'x' }))).toEqual([
      'Adresse e-mail invalide',
    ])
    expect(loginSchema.parse({ email: '  roua@example.com ', password: 'x' }).email).toBe(
      'roua@example.com',
    )
  })
})

describe('registerSchema', () => {
  const valid = {
    full_name: '',
    email: 'a@example.com',
    password: 'Motdepasse1',
    confirmPassword: 'Motdepasse1',
  }

  it('accepts valid data, with an optional name', () => {
    expect(registerSchema.safeParse(valid).success).toBe(true)
  })

  it('enforces the backend password limits (8 to 128 characters)', () => {
    expect(
      messages(registerSchema.safeParse({ ...valid, password: 'short', confirmPassword: 'short' })),
    ).toContain('Au moins 8 caractères')
    const long = 'x'.repeat(129)
    expect(
      messages(registerSchema.safeParse({ ...valid, password: long, confirmPassword: long })),
    ).toContain('128 caractères maximum')
  })

  it('checks the confirmation', () => {
    const result = registerSchema.safeParse({ ...valid, confirmPassword: 'Different1' })
    expect(messages(result)).toEqual(['Les mots de passe ne correspondent pas'])
  })
})

describe('profileFormSchema', () => {
  it('accepts an empty profile', () => {
    expect(profileFormSchema.safeParse(profile()).success).toBe(true)
  })

  it('applies the text limits of the backend', () => {
    expect(profileFormSchema.safeParse(profile({ summary: 'x'.repeat(2001) })).success).toBe(false)
    expect(profileFormSchema.safeParse(profile({ summary: 'x'.repeat(2000) })).success).toBe(true)
    expect(profileFormSchema.safeParse(profile({ skills: ['x'.repeat(81)] })).success).toBe(false)
    expect(profileFormSchema.safeParse(profile({ skills: Array(101).fill('a') })).success).toBe(
      false,
    )
  })

  it('requires the school, company and title of each item', () => {
    const result = profileFormSchema.safeParse(
      profile({ education: [emptyEducation()], experiences: [emptyExperience()] }),
    )
    expect(messages(result)).toEqual([
      "L'établissement est obligatoire",
      "L'entreprise est obligatoire",
      'Le poste est obligatoire',
    ])
  })

  it('checks years: 1950-2100 and end not before start', () => {
    const school = { ...emptyEducation(), school: 'ENIT' }
    const check = (start: string, end: string) =>
      messages(
        profileFormSchema.safeParse(
          profile({ education: [{ ...school, start_year: start, end_year: end }] }),
        ),
      )
    expect(check('1949', '')).toEqual(['Année entre 1950 et 2100'])
    expect(check('20ab', '')).toEqual(['Année entre 1950 et 2100'])
    expect(check('2024', '2022')).toEqual(['La fin ne peut pas précéder le début'])
    expect(check('2022', '2024')).toEqual([])
    expect(check('', '')).toEqual([])
  })
})

describe('preferencesFormSchema', () => {
  const valid = {
    contract_types: ['internship'],
    locations: ['Tunis'],
    domains: [],
    remote_ok: true,
    willing_to_relocate: false,
  }

  it('accepts the contract types known by the backend only', () => {
    expect(preferencesFormSchema.safeParse(valid).success).toBe(true)
    expect(
      preferencesFormSchema.safeParse({ ...valid, contract_types: ['freelance'] }).success,
    ).toBe(false)
  })

  it('limits the lists to 20 items of 100 characters', () => {
    expect(
      preferencesFormSchema.safeParse({ ...valid, locations: Array(21).fill('a') }).success,
    ).toBe(false)
    expect(preferencesFormSchema.safeParse({ ...valid, domains: ['x'.repeat(101)] }).success).toBe(
      false,
    )
  })
})
