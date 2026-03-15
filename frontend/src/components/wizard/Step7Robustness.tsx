import { useState } from 'react';
import Plot from 'react-plotly.js';
import api from '../../api/client';
import type { RobustnessResults } from '../../types';

interface Props {
  projectId: number;
  robustness: RobustnessResults | null;
  onRobustnessLoaded: (results: RobustnessResults) => void;
}

export default function Step7Robustness({ projectId, robustness, onRobustnessLoaded }: Props) {
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState('');

  const runRobustness = async () => {
    setRunning(true);
    setError('');
    try {
      const res = await api.post(`/projects/${projectId}/robustness`);
      onRobustnessLoaded(res.data);
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Robustness analysis failed');
      } else {
        setError('Robustness analysis failed');
      }
    } finally {
      setRunning(false);
    }
  };

  const handleExport = async (format: 'csv' | 'pdf') => {
    setDownloading(format);
    try {
      const res = await api.get(`/projects/${projectId}/export/${format}`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `af-results.${format === 'csv' ? 'zip' : 'pdf'}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError(`Failed to download ${format.toUpperCase()}`);
    } finally {
      setDownloading('');
    }
  };

  return (
    <div className="step-content">
      <h3>Step 7: Robustness & Export</h3>
      <p className="step-description">
        Test the robustness of your results by varying the poverty cutoff k and
        examining the impact of removing individual indicators.
      </p>

      {!robustness && (
        <div className="action-area">
          <button
            className="btn btn-primary btn-lg"
            onClick={runRobustness}
            disabled={running}
          >
            {running ? 'Running Robustness Analysis...' : 'Run Robustness Analysis'}
          </button>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      {robustness && (
        <>
          <div className="section">
            <h4>K-Robustness</h4>
            <p className="helper-text">
              How do the headline measures change as the poverty cutoff k varies?
            </p>
            <div className="chart-container">
              <Plot
                data={[
                  {
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'H',
                    x: robustness.k_robustness.map((r) => r.k),
                    y: robustness.k_robustness.map((r) => r.H),
                    marker: { color: '#2563eb' },
                  },
                  {
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'A',
                    x: robustness.k_robustness.map((r) => r.k),
                    y: robustness.k_robustness.map((r) => r.A),
                    marker: { color: '#7c3aed' },
                  },
                  {
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'M0',
                    x: robustness.k_robustness.map((r) => r.k),
                    y: robustness.k_robustness.map((r) => r.M0),
                    marker: { color: '#dc2626' },
                  },
                ]}
                layout={{
                  title: { text: 'Sensitivity to Poverty Cutoff k' },
                  xaxis: { title: { text: 'Poverty Cutoff (k)' } },
                  yaxis: { title: { text: 'Value' } },
                  margin: { l: 60, r: 30, t: 50, b: 50 },
                  height: 400,
                  legend: { orientation: 'h', y: -0.2 },
                  paper_bgcolor: 'transparent',
                  plot_bgcolor: 'transparent',
                }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%' }}
              />
            </div>
          </div>

          {robustness.leave_one_out && robustness.leave_one_out.length > 0 && (
            <div className="section">
              <h4>Leave-One-Out Analysis</h4>
              <p className="helper-text">
                How does M0 change when each indicator is removed from the index?
              </p>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Dropped Indicator</th>
                      <th>H</th>
                      <th>A</th>
                      <th>M0</th>
                    </tr>
                  </thead>
                  <tbody>
                    {robustness.leave_one_out.map((row) => (
                      <tr key={row.dropped_indicator}>
                        <td><strong>{row.dropped_indicator}</strong></td>
                        <td>{(row.H * 100).toFixed(2)}%</td>
                        <td>{(row.A * 100).toFixed(2)}%</td>
                        <td>{row.M0.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      <div className="section">
        <h4>Export Results</h4>
        <div className="export-buttons">
          <button
            className="btn btn-primary"
            onClick={() => handleExport('csv')}
            disabled={downloading === 'csv'}
          >
            {downloading === 'csv' ? 'Downloading...' : 'Download CSV (ZIP)'}
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => handleExport('pdf')}
            disabled={downloading === 'pdf'}
          >
            {downloading === 'pdf' ? 'Downloading...' : 'Download PDF Report'}
          </button>
        </div>
      </div>
    </div>
  );
}
