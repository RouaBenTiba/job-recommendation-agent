import { zodResolver } from '@hookform/resolvers/zod'
import { Briefcase, FileText, GraduationCap, Plus, Trash2, Wrench } from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'
import { Controller, useFieldArray, useForm, useWatch } from 'react-hook-form'
import { isApiError } from '../api/client'
import type { Profile, ProfileUpdate } from '../api/types'
import { Completeness, type CompletenessSection } from './Completeness'
import { Notice } from './Notice'
import { ProfilePreview } from './ProfilePreview'
import { TagInput } from './TagInput'
import { TextArea, TextField } from './TextField'
import {
  buildProfileUpdate,
  emptyEducation,
  emptyExperience,
  profileToForm,
} from '../lib/profileForm'
import { profileFormSchema, type ProfileFormValues } from '../lib/schemas'
import { applyServerErrors } from '../lib/serverErrors'

function SectionHead({ icon, title }: { icon: ReactNode; title: string }) {
  return (
    <div className="doc-head">
      {icon}
      <h2>{title}</h2>
    </div>
  )
}

function completenessOf(values: ProfileFormValues): CompletenessSection[] {
  return [
    { label: 'Résumé', done: values.summary.trim() !== '' },
    { label: 'Compétences', done: values.skills.length > 0 },
    { label: 'Technologies', done: values.technologies.length > 0 },
    { label: 'Formation', done: values.education.some((item) => item.school.trim() !== '') },
    {
      label: 'Expériences',
      done: values.experiences.some(
        (item) => item.company.trim() !== '' && item.title.trim() !== '',
      ),
    },
  ]
}

interface ProfileEditorProps {
  profile: Profile | null
  ownerName: string
  onSave: (update: ProfileUpdate) => Promise<unknown>
  children?: ReactNode
}

export function ProfileEditor({ profile, ownerName, onSave, children }: ProfileEditorProps) {
  const initial = useMemo(() => profileToForm(profile), [profile])
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    control,
    handleSubmit,
    reset,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: initial,
  })
  const education = useFieldArray({ control, name: 'education' })
  const experiences = useFieldArray({ control, name: 'experiences' })

  const current = useWatch({ control }) as ProfileFormValues
  const hasChanges = Object.keys(buildProfileUpdate(current, initial)).length > 0

  const onSubmit = async (values: ProfileFormValues) => {
    setServerError(null)
    const update = buildProfileUpdate(values, initial)
    if (Object.keys(update).length === 0) return
    try {
      await onSave(update)
    } catch (error) {
      if (!isApiError(error)) throw error
      setServerError(
        applyServerErrors(setError, error.fieldErrors)
          ? 'Corrigez les champs signalés.'
          : error.message,
      )
    }
  }

  return (
    <div className="profile-layout">
      <div className="editor-col">
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="document">
            <section className="doc-section">
              <SectionHead icon={<FileText size={22} aria-hidden="true" />} title="Présentation" />
              <TextArea label="Résumé" error={errors.summary?.message} {...register('summary')} />
              <TextArea
                label="Objectif professionnel"
                error={errors.objectives?.message}
                {...register('objectives')}
              />
            </section>

            <section className="doc-section">
              <SectionHead
                icon={<Wrench size={22} aria-hidden="true" />}
                title="Compétences et outils"
              />
              <Controller
                control={control}
                name="skills"
                render={({ field }) => (
                  <TagInput
                    label="Compétences"
                    value={field.value}
                    onChange={field.onChange}
                    error={errors.skills?.message}
                  />
                )}
              />
              <Controller
                control={control}
                name="technologies"
                render={({ field }) => (
                  <TagInput
                    label="Technologies"
                    value={field.value}
                    onChange={field.onChange}
                    error={errors.technologies?.message}
                  />
                )}
              />
              <Controller
                control={control}
                name="interests"
                render={({ field }) => (
                  <TagInput
                    label="Centres d'intérêt"
                    value={field.value}
                    onChange={field.onChange}
                    error={errors.interests?.message}
                  />
                )}
              />
            </section>

            <section className="doc-section">
              <SectionHead
                icon={<GraduationCap size={22} aria-hidden="true" />}
                title="Formation"
              />
              {education.fields.map((item, index) => {
                const fieldErrors = errors.education?.[index]
                return (
                  <fieldset key={item.id} className="entry">
                    <legend>Formation {index + 1}</legend>
                    <TextField
                      label="Établissement"
                      error={fieldErrors?.school?.message}
                      {...register(`education.${index}.school`)}
                    />
                    <TextField
                      label="Diplôme"
                      error={fieldErrors?.degree?.message}
                      {...register(`education.${index}.degree`)}
                    />
                    <TextField
                      label="Spécialité"
                      error={fieldErrors?.field_of_study?.message}
                      {...register(`education.${index}.field_of_study`)}
                    />
                    <div className="row">
                      <TextField
                        label="Début (année)"
                        inputMode="numeric"
                        error={fieldErrors?.start_year?.message}
                        {...register(`education.${index}.start_year`)}
                      />
                      <TextField
                        label="Fin (année)"
                        inputMode="numeric"
                        error={fieldErrors?.end_year?.message}
                        {...register(`education.${index}.end_year`)}
                      />
                    </div>
                    <button
                      type="button"
                      className="ghost-danger"
                      onClick={() => education.remove(index)}
                    >
                      <Trash2 size={16} aria-hidden="true" />
                      Supprimer la formation {index + 1}
                    </button>
                  </fieldset>
                )
              })}
              {errors.education?.message && (
                <p className="field-error" role="alert">
                  {errors.education.message}
                </p>
              )}
              <button
                type="button"
                className="secondary"
                onClick={() => education.append(emptyEducation())}
              >
                <Plus size={16} aria-hidden="true" />
                Ajouter une formation
              </button>
            </section>

            <section className="doc-section">
              <SectionHead icon={<Briefcase size={22} aria-hidden="true" />} title="Expériences" />
              {experiences.fields.map((item, index) => {
                const fieldErrors = errors.experiences?.[index]
                return (
                  <fieldset key={item.id} className="entry">
                    <legend>Expérience {index + 1}</legend>
                    <TextField
                      label="Entreprise"
                      error={fieldErrors?.company?.message}
                      {...register(`experiences.${index}.company`)}
                    />
                    <TextField
                      label="Poste"
                      error={fieldErrors?.title?.message}
                      {...register(`experiences.${index}.title`)}
                    />
                    <div className="row">
                      <TextField
                        label="Début"
                        hint="Ex. 2024 ou 2024-06"
                        error={fieldErrors?.start?.message}
                        {...register(`experiences.${index}.start`)}
                      />
                      <TextField
                        label="Fin"
                        hint="Vide si en cours"
                        error={fieldErrors?.end?.message}
                        {...register(`experiences.${index}.end`)}
                      />
                    </div>
                    <TextArea
                      label="Description"
                      error={fieldErrors?.description?.message}
                      {...register(`experiences.${index}.description`)}
                    />
                    <Controller
                      control={control}
                      name={`experiences.${index}.technologies`}
                      render={({ field }) => (
                        <TagInput
                          label="Technologies utilisées"
                          value={field.value}
                          onChange={field.onChange}
                          error={fieldErrors?.technologies?.message}
                        />
                      )}
                    />
                    <button
                      type="button"
                      className="ghost-danger"
                      onClick={() => experiences.remove(index)}
                    >
                      <Trash2 size={16} aria-hidden="true" />
                      Supprimer l&apos;expérience {index + 1}
                    </button>
                  </fieldset>
                )
              })}
              {errors.experiences?.message && (
                <p className="field-error" role="alert">
                  {errors.experiences.message}
                </p>
              )}
              <button
                type="button"
                className="secondary"
                onClick={() => experiences.append(emptyExperience())}
              >
                <Plus size={16} aria-hidden="true" />
                Ajouter une expérience
              </button>
            </section>
          </div>

          {serverError && (
            <Notice tone="error" role="alert">
              {serverError}
            </Notice>
          )}
          <div className="action-bar">
            <p className={hasChanges ? 'action-state is-dirty' : 'action-state'} aria-live="polite">
              {hasChanges ? 'Modifications non enregistrées' : 'Aucune modification'}
            </p>
            <div className="action-buttons">
              <button
                type="button"
                className="secondary"
                disabled={!hasChanges}
                onClick={() => reset(initial)}
              >
                Annuler les modifications
              </button>
              <button type="submit" disabled={!hasChanges || isSubmitting}>
                {isSubmitting ? 'Enregistrement…' : 'Enregistrer'}
              </button>
            </div>
          </div>
        </form>
        {children}
      </div>

      <aside className="preview-col" aria-label="Aperçu du profil">
        <Completeness sections={completenessOf(current)} />
        <ProfilePreview values={current} name={ownerName} version={profile?.version ?? null} />
      </aside>
    </div>
  )
}
