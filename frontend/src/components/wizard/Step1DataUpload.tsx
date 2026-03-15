import { useState, useRef } from 'react';
import api from '../../api/client';
import type { ColumnMetadata } from '../../types';

interface Props {
  projectId: number;
  onColumnsLoaded: (columns: ColumnMetadata[]) => void;
}

export default function Step1DataUpload({ projectId, onColumnsLoaded }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState<Record<string, unknown>[]>([]);
  const [columns, setColumns] = useState<ColumnMetadata[]>([]);
  const [fileName, setFileName] = useState('');

  const handleFileChange = () => {
    const file = fileRef.current?.files?.[0];
    if (file) {
      setFileName(file.name);
    }
  };

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('file', file);
      await api.post(`/projects/${projectId}/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // Load preview and columns
      const [previewRes, columnsRes] = await Promise.all([
        api.get(`/projects/${projectId}/data/preview`),
        api.get(`/projects/${projectId}/data/columns`),
      ]);

      setPreview(previewRes.data);
      setColumns(columnsRes.data);
      onColumnsLoaded(columnsRes.data);
      setUploaded(true);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Upload failed');
      } else {
        setError('Upload failed');
      }
    } finally {
      setUploading(false);
    }
  };

  const previewColumns = preview.length > 0 ? Object.keys(preview[0]) : [];

  return (
    <div className="step-content">
      <h3>Step 1: Upload Your Data</h3>
      <p className="step-description">
        Upload a CSV or Excel file containing your survey data. Each row should represent
        an observation (household, individual, etc.) and each column an indicator or variable.
      </p>

      <div className="upload-area">
        <div className="file-input-wrapper">
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileChange}
            id="fileInput"
          />
          <label htmlFor="fileInput" className="file-label">
            {fileName || 'Choose a file (.csv, .xlsx)'}
          </label>
        </div>
        <button
          className="btn btn-primary"
          onClick={handleUpload}
          disabled={uploading || !fileName}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {uploaded && (
        <>
          <div className="section">
            <h4>Column Statistics</h4>
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>Type</th>
                    <th>Missing</th>
                    <th>Unique</th>
                    <th>Min</th>
                    <th>Max</th>
                    <th>Mean</th>
                  </tr>
                </thead>
                <tbody>
                  {columns.map((col) => (
                    <tr key={col.name}>
                      <td><strong>{col.name}</strong></td>
                      <td>{col.dtype}</td>
                      <td>{col.missing_count}</td>
                      <td>{col.unique_count}</td>
                      <td>{col.min != null ? col.min.toFixed(2) : '-'}</td>
                      <td>{col.max != null ? col.max.toFixed(2) : '-'}</td>
                      <td>{col.mean != null ? col.mean.toFixed(2) : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="section">
            <h4>Data Preview (first 20 rows)</h4>
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    {previewColumns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, i) => (
                    <tr key={i}>
                      {previewColumns.map((col) => (
                        <td key={col}>{String(row[col] ?? '')}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
