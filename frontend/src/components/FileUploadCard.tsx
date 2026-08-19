import { useRef, useState } from "react";
import "./FileUploadCard.css";

const ACCEPTED = ".csv,.xlsx,.xls,.docx,.pdf,.pptx";

interface Props {
  onSubmitFile: (file: File, instruction: string) => void;
  errorMessage: string | null;
}

export default function FileUploadCard({ onSubmitFile, errorMessage }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [instruction, setInstruction] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    onSubmitFile(file, instruction);
  };

  return (
    <form className="file-upload-card" onSubmit={handleSubmit}>
      <span className="file-upload-label">Or upload a document instead</span>
      <p className="file-upload-hint">CSV or Excel rows become the real data this workflow runs against. Word, PDF, or PowerPoint content is read as your problem description.</p>

      <div className="file-upload-row">
        <button type="button" className="btn-secondary file-upload-pick" onClick={() => inputRef.current?.click()}>
          {file ? file.name : "Choose file (.csv, .xlsx, .docx, .pdf, .pptx)"}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          className="sr-only"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      </div>

      <input
        type="text"
        className="file-upload-instruction"
        placeholder="Optional: add an instruction, e.g. 'flag risk_score above 50 and alert sales'"
        value={instruction}
        onChange={(e) => setInstruction(e.target.value)}
        maxLength={500}
      />

      <div className="file-upload-form-row">
        <span className="error-text">{errorMessage}</span>
        <button type="submit" className="btn-primary" disabled={!file}>
          Build From File
        </button>
      </div>
    </form>
  );
}
