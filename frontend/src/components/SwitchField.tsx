import { useId, type InputHTMLAttributes, type Ref } from 'react'

type SwitchFieldProps = {
  label: string
  description: string
  ref?: Ref<HTMLInputElement>
} & Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'role'>

/** An on/off setting. The explanation sits outside the label so the control keeps a short name. */
export function SwitchField({ label, description, ...input }: SwitchFieldProps) {
  const id = useId()
  return (
    <div className="switch-row">
      <div>
        <label htmlFor={id}>{label}</label>
        <p className="field-hint" id={`${id}-description`}>
          {description}
        </p>
      </div>
      <input
        id={id}
        type="checkbox"
        role="switch"
        className="switch"
        aria-describedby={`${id}-description`}
        {...input}
      />
    </div>
  )
}
