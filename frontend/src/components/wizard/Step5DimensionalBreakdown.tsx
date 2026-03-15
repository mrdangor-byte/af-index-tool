import Plot from 'react-plotly.js';
import type { AnalysisResults } from '../../types';

interface Props {
  results: AnalysisResults | null;
}

export default function Step5DimensionalBreakdown({ results }: Props) {
  if (!results) {
    return (
      <div className="step-content">
        <h3>Step 5: Dimensional Breakdown</h3>
        <div className="empty-state">
          <p>No results available. Please run the analysis in Step 3 first.</p>
        </div>
      </div>
    );
  }

  const breakdown = results.dimensional_breakdown;

  return (
    <div className="step-content">
      <h3>Step 5: Dimensional Breakdown</h3>
      <p className="step-description">
        Examine how each indicator contributes to overall poverty. This decomposition
        reveals which deprivations matter most.
      </p>

      <div className="section">
        <h4>Indicator Contributions</h4>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Indicator</th>
                <th>Dimension</th>
                <th>Weight</th>
                <th>Raw Headcount</th>
                <th>Censored Headcount</th>
                <th>Contribution (%)</th>
              </tr>
            </thead>
            <tbody>
              {breakdown.map((row) => (
                <tr key={row.indicator_name}>
                  <td><strong>{row.indicator_name}</strong></td>
                  <td>{row.dimension}</td>
                  <td>{row.weight.toFixed(4)}</td>
                  <td>{(row.raw_headcount * 100).toFixed(1)}%</td>
                  <td>{(row.censored_headcount * 100).toFixed(1)}%</td>
                  <td>{(row.contribution * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="charts-row">
        <div className="chart-container">
          <Plot
            data={[
              {
                type: 'bar',
                orientation: 'h',
                y: breakdown.map((r) => r.indicator_name),
                x: breakdown.map((r) => r.contribution * 100),
                marker: { color: '#2563eb' },
                hovertemplate: '%{y}: %{x:.1f}%<extra></extra>',
              },
            ]}
            layout={{
              title: { text: 'Percentage Contribution to M0' },
              xaxis: { title: { text: 'Contribution (%)' } },
              yaxis: { automargin: true },
              margin: { l: 150, r: 30, t: 50, b: 50 },
              height: Math.max(300, breakdown.length * 40 + 100),
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>

        <div className="chart-container">
          <Plot
            data={[
              {
                type: 'bar',
                name: 'Raw',
                x: breakdown.map((r) => r.indicator_name),
                y: breakdown.map((r) => r.raw_headcount * 100),
                marker: { color: '#94a3b8' },
              },
              {
                type: 'bar',
                name: 'Censored',
                x: breakdown.map((r) => r.indicator_name),
                y: breakdown.map((r) => r.censored_headcount * 100),
                marker: { color: '#2563eb' },
              },
            ]}
            layout={{
              title: { text: 'Headcount Ratios (%)' },
              barmode: 'group',
              yaxis: { title: { text: 'Headcount (%)' } },
              xaxis: { automargin: true },
              margin: { l: 60, r: 30, t: 50, b: 100 },
              height: 400,
              legend: { orientation: 'h', y: -0.3 },
              paper_bgcolor: 'transparent',
              plot_bgcolor: 'transparent',
            }}
            config={{ responsive: true, displayModeBar: false }}
            style={{ width: '100%' }}
          />
        </div>
      </div>
    </div>
  );
}
