import { useState } from 'react';
import type { ChangeEvent } from 'react';

type Props = {
  id: string;
  label: string;
  value: string;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  autoComplete: string;
  placeholder?: string;
  minLength?: number;
};

export default function PasswordField({ id, label, value, onChange, autoComplete, placeholder = 'Enter your password', minLength }: Props) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="field-group">
      <label htmlFor={id}>{label}</label>
      <div className="password-wrapper">
        <input id={id} name={id} type={visible ? 'text' : 'password'} value={value} onChange={onChange}
          autoComplete={autoComplete} placeholder={placeholder} minLength={minLength} required />
        <button type="button" className="show-password" onClick={() => setVisible(!visible)} aria-label={`${visible ? 'Hide' : 'Show'} ${label.toLowerCase()}`}>
          {visible ? 'Hide' : 'Show'}
        </button>
      </div>
    </div>
  );
}
