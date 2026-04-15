import { useState, useRef } from 'react';
import { signUpload, uploadFileToS3 } from '../services/api';

interface UploadedFile {
  file: File;
  preview: string;
  storageKey: string | null;
  uploading: boolean;
  error: string | null;
}

interface ImageUploadProps {
  maxFiles?: number;
  onKeysChange: (keys: string[]) => void;
}

export default function ImageUpload({ maxFiles = 5, onKeysChange }: ImageUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (selectedFiles: FileList) => {
    const newFiles: UploadedFile[] = [];
    const remaining = maxFiles - files.length;

    for (let i = 0; i < Math.min(selectedFiles.length, remaining); i++) {
      const file = selectedFiles[i];
      const allowed = ['image/jpeg', 'image/png', 'image/webp'];
      if (!allowed.includes(file.type)) continue;
      if (file.size > 10 * 1024 * 1024) continue;

      newFiles.push({
        file,
        preview: URL.createObjectURL(file),
        storageKey: null,
        uploading: true,
        error: null,
      });
    }

    const updatedFiles = [...files, ...newFiles];
    setFiles(updatedFiles);

    // Upload each new file
    for (const uf of newFiles) {
      try {
        const signed = await signUpload(uf.file.name, uf.file.type, uf.file.size);
        await uploadFileToS3(signed.upload_url, uf.file);
        uf.storageKey = signed.storage_key;
        uf.uploading = false;
      } catch {
        uf.error = 'Upload failed';
        uf.uploading = false;
      }
    }

    setFiles([...updatedFiles]);
    const keys = updatedFiles
      .filter((f) => f.storageKey)
      .map((f) => f.storageKey!);
    onKeysChange(keys);
  };

  const removeFile = (index: number) => {
    const updated = files.filter((_, i) => i !== index);
    setFiles(updated);
    const keys = updated.filter((f) => f.storageKey).map((f) => f.storageKey!);
    onKeysChange(keys);
  };

  return (
    <div>
      <div className="flex flex-wrap gap-3 mb-3">
        {files.map((f, i) => (
          <div key={i} className="relative w-24 h-24 rounded-lg overflow-hidden border-2 border-gray-200">
            <img src={f.preview} alt="" className="w-full h-full object-cover" />
            {f.uploading && (
              <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
              </div>
            )}
            {f.error && (
              <div className="absolute inset-0 bg-red-500/50 flex items-center justify-center text-white text-xs">
                Error
              </div>
            )}
            <button
              onClick={() => removeFile(i)}
              className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600"
            >
              ×
            </button>
          </div>
        ))}
        {files.length < maxFiles && (
          <button
            onClick={() => inputRef.current?.click()}
            className="w-24 h-24 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center text-gray-400 hover:border-primary-400 hover:text-primary-500 transition-colors"
          >
            <span className="text-2xl">+</span>
            <span className="text-xs">Add Photo</span>
          </button>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        multiple
        className="hidden"
        onChange={(e) => e.target.files && handleFiles(e.target.files)}
      />
      <p className="text-xs text-gray-500">
        Upload 1–{maxFiles} images (JPEG, PNG, WebP). Max 10 MB each.
      </p>
    </div>
  );
}
