import type { AnalysisResults } from '../../types';

interface Props {
  results: AnalysisResults | null;
}

export default function Step4Aggregation({ results }: Props) {
  if (!results) {
    return (
      <div className="step-content">
        <h3>Step 4: Aggregation</h3>
        <div className="empty-state">
          <p>No results available. Please run the analysis in Step 3 first.</p>
        </div>
      </div>
    );
  }

  const { headline } = results;

  return (
    <div className="step-content">
      <h3>Step 4: Aggregation</h3>
      <p className="step-description">
        The adjusted headcount ratio M0 captures both the incidence and intensity of poverty.
      </p>

      <div className="headline-cards">
        <div className="stat-card stat-card-primary">
          <div className="stat-icon">H</div>
          <div className="stat-value">{(headline.H * 100).toFixed(2)}%</div>
          <div className="stat-label">Incidence (Headcount Ratio)</div>
          <div className="stat-desc">Share of the population that is MPI-poor</div>
        </div>
        <div className="stat-card stat-card-primary">
          <div className="stat-icon">A</div>
          <div className="stat-value">{(headline.A * 100).toFixed(2)}%</div>
          <div className="stat-label">Intensity (Average Deprivation Share)</div>
          <div className="stat-desc">Average deprivation score among the poor</div>
        </div>
        <div className="stat-card stat-card-accent">
          <div className="stat-icon">M0</div>
          <div className="stat-value">{headline.M0.toFixed(4)}</div>
          <div className="stat-label">Adjusted Headcount Ratio</div>
          <div className="stat-desc">M0 = H x A</div>
        </div>
      </div>

      <div className="formula-display">
        <div className="formula">
          M<sub>0</sub> = H &times; A = {(headline.H * 100).toFixed(2)}% &times; {(headline.A * 100).toFixed(2)}% = <strong>{headline.M0.toFixed(4)}</strong>
        </div>
      </div>

      <div className="counts-row">
        <div className="count-item">
          <span className="count-label">Poor (q):</span>
          <span className="count-value">{headline.q.toLocaleString()}</span>
        </div>
        <div className="count-item">
          <span className="count-label">Total (n):</span>
          <span className="count-value">{headline.n.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
