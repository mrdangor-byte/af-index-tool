import { useState } from 'react';
import api from '../../api/client';
import type { AnalysisResults } from '../../types';

interface Props {
  projectId: number;
  results: AnalysisResults | null;
  onResultsLoaded: (results: AnalysisResults) => void;
}

export default function Step3Identification({ projectId, results, onResultsLoaded }: Props) {
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

  const runAnalysis = async () => {
    setRunning(true);
    setError('');
    try {
      await api.post(`/projects/${projectId}/analyze`);
      const res = await api.get(`/projects/${projectId}/results`);
      onResultsLoaded(res.data);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Analysis failed');
      } else {
        setError('Analysis failed');
      }
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="step-content">
      <h3>Step 3: Identification</h3>
      <p className="step-description">
        Apply the dual-cutoff method to identify who is multidimensionally poor.
        First, each indicator cutoff identifies deprivations. Then, the poverty cutoff k
        determines who is considered poor based on their weighted deprivation score.
      </p>

      {!results && (
        <div className="action-area">
          <button
            className="btn btn-primary btn-lg"
            onClick={runAnalysis}
            disabled={running}
          >
            {running ? 'Running Analysis...' : 'Run Analysis'}
          </button>
          <p className="helper-text">
            This will compute the deprivation matrix and identify the poor.
          </p>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      {results && (
        <div className="results-section">
          <div className="identification-summary">
            <div className="stat-card stat-card-large">
              <div className="stat-value">{results.headline.q.toLocaleString()}</div>
              <div className="stat-label">of {results.headline.n.toLocaleString()} observations identified as poor</div>
            </div>
            <div className="stat-card stat-card-large">
              <div className="stat-value">{(results.headline.H * 100).toFixed(1)}%</div>
              <div className="stat-label">Incidence of Poverty (H)</div>
            </div>
          </div>

          <div className="section">
            <h4>Interpretation</h4>
            <p>
              Using the dual-cutoff identification method, <strong>{results.headline.q.toLocaleString()}</strong> out
              of <strong>{results.headline.n.toLocaleString()}</strong> observations
              ({(results.headline.H * 100).toFixed(1)}%) are identified as multidimensionally poor.
              These are individuals whose weighted deprivation score meets or exceeds the poverty cutoff k.
            </p>
            <p>
              Proceed to Step 4 to see the aggregated headline measures (H, A, M0).
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
