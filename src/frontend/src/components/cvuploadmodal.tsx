
import { useEffect, useRef, useState } from 'react';
import '../cv-upload-modal.css';

type Props = {
  open: boolean;
  onClose: () => void;
  onAnalyze: (file: File) => Promise<void>;
};

const MAX_SIZE = 5 * 1024 * 1024;

export default function CvUploadModal({
  open,
  onClose,
  onAnalyze,
}: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;

    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  useEffect(() => {
    if (!open) {
      setFile(null);
      setError('');
      setDragging(false);
    }
  }, [open]);

  function selectFile(next?: File) {
    if (!next) return;

    setError('');

    if (!/\.(pdf|docx)$/i.test(next.name)) {
      setFile(null);
      setError('Please select a PDF or DOCX file.');
      return;
    }

    if (next.size === 0 || next.size > MAX_SIZE) {
      setFile(null);
      setError('Your CV must be between 1 byte and 5 MB.');
      return;
    }

    setFile(next);
  }

  async function analyze() {
    if (!file || busy) return;

    setBusy(true);
    setError('');

    try {
      await onAnalyze(file);
      onClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'CV analysis failed.'
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className="cf-cv-dialog"
      aria-labelledby="cf-cv-dialog-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <div className="cf-cv-dialog-heading">
        <div>
          <h2 id="cf-cv-dialog-title">Upload your CV</h2>
          <p>
            CareerForge will extract skills and analyse
            your experience.
          </p>
        </div>

        <button
          type="button"
          className="cf-cv-dialog-close"
          aria-label="Close upload dialog"
          disabled={busy}
          onClick={onClose}
        >
          ×
        </button>
      </div>

      <input
        ref={inputRef}
        type="file"
        hidden
        accept=".pdf,.docx"
        onChange={(event) => {
          selectFile(event.target.files?.[0]);
          event.target.value = '';
        }}
      />

      <button
        type="button"
        className={`cf-cv-dropzone ${dragging ? 'is-dragging' : ''}`}
        disabled={busy}
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          if (!busy) setDragging(true);
        }}
        onDragLeave={(event) => {
          event.preventDefault();
          setDragging(false);
        }}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          if (!busy) selectFile(event.dataTransfer.files[0]);
        }}
      >
        <span className="cf-cv-drop-icon">
          {file ? '✓' : '+'}
        </span>

        <strong>
          {file ? file.name : 'Drag and drop your CV here'}
        </strong>

        <span>
          {file
            ? `${(file.size / 1024 / 1024).toFixed(2)} MB · Click to change`
            : 'or click to browse your files'}
        </span>

        <small>PDF or DOCX · Maximum 5 MB</small>
      </button>

      {error && (
        <p className="cf-cv-dialog-error" role="alert">
          {error}
        </p>
      )}

      <div className="cf-cv-dialog-actions">
        <button
          type="button"
          className="cf-cv-cancel"
          disabled={busy}
          onClick={onClose}
        >
          Cancel
        </button>

        <button
          type="button"
          className="cf-cv-analyze"
          disabled={!file || busy}
          onClick={() => void analyze()}
        >
          {busy ? 'Analyzing...' : 'Analyze CV'}
        </button>
      </div>
    </dialog>
  );
}
