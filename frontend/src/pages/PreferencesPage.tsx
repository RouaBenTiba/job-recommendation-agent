import { zodResolver } from '@hookform/resolvers/zod'
import {
  Building2,
  Check,
  Clock,
  FileText,
  GraduationCap,
  Repeat,
  type LucideIcon,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { isApiError } from '../api/client'
import {
  CONTRACT_LABELS,
  CONTRACT_TYPES,
  type ContractType,
  type Preferences,
  type PreferencesUpdate,
} from '../api/types'
import { Notice } from '../components/Notice'
import { Spinner } from '../components/Spinner'
import { SwitchField } from '../components/SwitchField'
import { TagInput } from '../components/TagInput'
import { usePreferences, useSavePreferences } from '../hooks/usePreferences'
import { preferencesFormSchema, type PreferencesFormValues } from '../lib/schemas'
import { applyServerErrors } from '../lib/serverErrors'

const CONTRACT_ICONS: Record<ContractType, LucideIcon> = {
  internship: GraduationCap,
  apprenticeship: Repeat,
  full_time: Building2,
  part_time: Clock,
  contract: FileText,
}

function toForm(preferences: Preferences): PreferencesFormValues {
  return {
    contract_types: CONTRACT_TYPES.filter((type) => preferences.contract_types.includes(type)),
    locations: [...preferences.locations],
    domains: [...preferences.domains],
    remote_ok: preferences.remote_ok,
    willing_to_relocate: preferences.willing_to_relocate,
  }
}

interface PreferencesFormProps {
  preferences: Preferences
  onSave: (data: PreferencesUpdate) => Promise<unknown>
  saved: boolean
}

function PreferencesForm({ preferences, onSave, saved }: PreferencesFormProps) {
  const initial = useMemo(() => toForm(preferences), [preferences])
  const [serverError, setServerError] = useState<string | null>(null)
  const {
    register,
    control,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<PreferencesFormValues>({
    resolver: zodResolver(preferencesFormSchema),
    defaultValues: initial,
  })

  const current = useWatch({ control }) as PreferencesFormValues
  const hasChanges = JSON.stringify(current) !== JSON.stringify(initial)

  const onSubmit = async (values: PreferencesFormValues) => {
    setServerError(null)
    try {
      await onSave(values)
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
    <form onSubmit={handleSubmit(onSubmit)} noValidate>
      <div className="document">
        <section className="doc-section">
          <Controller
            control={control}
            name="contract_types"
            render={({ field }) => (
              <fieldset className="plain">
                <legend>Types de contrat recherchés</legend>
                <div className="tiles">
                  {CONTRACT_TYPES.map((type) => {
                    const Icon = CONTRACT_ICONS[type]
                    const on = field.value.includes(type)
                    return (
                      <label key={type} className={on ? 'tile is-on' : 'tile'}>
                        <input
                          type="checkbox"
                          checked={on}
                          onChange={(event) =>
                            field.onChange(
                              event.target.checked
                                ? [...field.value, type]
                                : field.value.filter((item) => item !== type),
                            )
                          }
                        />
                        <Icon size={20} aria-hidden="true" />
                        {CONTRACT_LABELS[type]}
                        <span className="tile-check" aria-hidden="true">
                          {on && <Check size={14} />}
                        </span>
                      </label>
                    )
                  })}
                </div>
                {errors.contract_types?.message && (
                  <p className="field-error" role="alert">
                    {errors.contract_types.message}
                  </p>
                )}
              </fieldset>
            )}
          />
        </section>

        <section className="doc-section">
          <Controller
            control={control}
            name="locations"
            render={({ field }) => (
              <TagInput
                label="Localisations"
                hint="Villes, régions ou pays (20 maximum)."
                value={field.value}
                onChange={field.onChange}
                error={errors.locations?.message}
              />
            )}
          />
          <Controller
            control={control}
            name="domains"
            render={({ field }) => (
              <TagInput
                label="Domaines"
                hint="Ex. Data, Cloud, Développement web (20 maximum)."
                value={field.value}
                onChange={field.onChange}
                error={errors.domains?.message}
              />
            )}
          />
        </section>

        <section className="doc-section">
          <SwitchField
            label="Télétravail accepté"
            description="Les offres à distance seront prises en compte."
            {...register('remote_ok')}
          />
          <SwitchField
            label="Prête à déménager"
            description="Les offres hors de vos localisations pourront apparaître."
            {...register('willing_to_relocate')}
          />
        </section>
      </div>

      {serverError && (
        <Notice tone="error" role="alert">
          {serverError}
        </Notice>
      )}
      {saved && !hasChanges && (
        <Notice tone="success" role="status">
          Préférences enregistrées.
        </Notice>
      )}
      <div className="action-bar">
        <p className={hasChanges ? 'action-state is-dirty' : 'action-state'} aria-live="polite">
          {hasChanges ? 'Modifications non enregistrées' : 'Aucune modification'}
        </p>
        <div className="action-buttons">
          <button type="submit" disabled={!hasChanges || isSubmitting}>
            {isSubmitting ? 'Enregistrement…' : 'Enregistrer'}
          </button>
        </div>
      </div>
    </form>
  )
}

export function PreferencesPage() {
  const preferences = usePreferences()
  const save = useSavePreferences()

  if (preferences.isPending) return <Spinner />
  if (preferences.isError)
    return <p role="alert">Impossible de charger vos préférences. Réessayez plus tard.</p>

  return (
    <div className="page page-narrow">
      <header className="page-head">
        <div>
          <h1>Mes préférences</h1>
          <p className="lede">
            Elles servent à filtrer et à classer les offres qui vous sont recommandées.
          </p>
        </div>
      </header>
      <PreferencesForm
        key={preferences.data.updated_at ?? 'default'}
        preferences={preferences.data}
        onSave={save.mutateAsync}
        saved={save.isSuccess}
      />
    </div>
  )
}
