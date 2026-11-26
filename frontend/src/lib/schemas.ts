import { z } from 'zod'
import { CONTRACT_TYPES } from '../api/types'

// The limits mirror the backend schemas (app/schemas/*.py): same rules on both sides.

const required = (label: string, max: number) =>
  z.string().trim().min(1, `${label} est obligatoire`).max(max, `${max} caractères maximum`)

const optional = (max: number) => z.string().trim().max(max, `${max} caractères maximum`)

const email = z
  .string()
  .trim()
  .min(1, "L'adresse e-mail est obligatoire")
  .pipe(z.email('Adresse e-mail invalide'))

export const loginSchema = z.object({
  email,
  password: z.string().min(1, 'Le mot de passe est obligatoire'),
})
export type LoginValues = z.infer<typeof loginSchema>

export const registerSchema = z
  .object({
    full_name: optional(150),
    email,
    password: z.string().min(8, 'Au moins 8 caractères').max(128, '128 caractères maximum'),
    confirmPassword: z.string(),
  })
  .refine((values) => values.password === values.confirmPassword, {
    path: ['confirmPassword'],
    message: 'Les mots de passe ne correspondent pas',
  })
export type RegisterValues = z.infer<typeof registerSchema>

const tagList = (maxItems: number, maxLength: number) =>
  z
    .array(z.string().trim().min(1).max(maxLength, `${maxLength} caractères maximum par élément`))
    .max(maxItems, `${maxItems} éléments maximum`)

// Years are typed in text inputs: they are strings in the form and numbers in the API.
const year = z
  .string()
  .trim()
  .refine(
    (value) =>
      value === '' || (/^\d{4}$/.test(value) && Number(value) >= 1950 && Number(value) <= 2100),
    {
      message: 'Année entre 1950 et 2100',
    },
  )

const educationSchema = z
  .object({
    school: required("L'établissement", 100),
    degree: optional(100),
    field_of_study: optional(100),
    start_year: year,
    end_year: year,
  })
  .refine(
    (item) =>
      !item.start_year || !item.end_year || Number(item.end_year) >= Number(item.start_year),
    {
      path: ['end_year'],
      message: 'La fin ne peut pas précéder le début',
    },
  )

const experienceSchema = z.object({
  company: required("L'entreprise", 100),
  title: required('Le poste', 100),
  start: optional(20),
  end: optional(20),
  description: optional(2000),
  technologies: tagList(30, 80),
})

export const profileFormSchema = z.object({
  summary: optional(2000),
  objectives: optional(2000),
  education: z.array(educationSchema).max(20, '20 formations maximum'),
  experiences: z.array(experienceSchema).max(30, '30 expériences maximum'),
  skills: tagList(100, 80),
  technologies: tagList(100, 80),
  interests: tagList(100, 80),
})
export type ProfileFormValues = z.infer<typeof profileFormSchema>

export const preferencesFormSchema = z.object({
  contract_types: z.array(z.enum(CONTRACT_TYPES)),
  locations: tagList(20, 100),
  domains: tagList(20, 100),
  remote_ok: z.boolean(),
  willing_to_relocate: z.boolean(),
})
export type PreferencesFormValues = z.infer<typeof preferencesFormSchema>
