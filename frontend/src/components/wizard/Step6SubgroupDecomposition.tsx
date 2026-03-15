import Plot from 'react-plotly.js';
import type { AnalysisResults } from '../../types';

interface Props {
  results: AnalysisResults | null;
  hasSubgroupColumn: boolean;
}

export default function Step6SubgroupDecomposition({ results, hasSubgroupColumn }: Props) {
  if (!hasSubgroupColumn) {
    return (
      <div className="step-content">
        <h3>Step 6: Subgroup Decomposition</h3>
        <div className="empty-state">
          <p>
            No subgroup column is configured. Go back to Step 2 and select a subgroup
            column (e.g., region, gender, urban/rural) to enable subgroup decomposition.
          </p>
        </div>
      </div>
    );
  }

  if (!results || !results.subgroup_decomposition || results.subgroup_decomposition.length === 0) {
    return (
      <div className="step-content">
        <h3>Step 6: Subgroup Decomposition</h3>
        <div className="empty-state">
          <p>No subgroup results available. Please run the analysis in Step 3 first.</p>
        </div>
      </div>
    );
  }

  const subgroups = results.subgroup_decomposition;

  return (
    <div className="step-content">
      <h3>Step 6: Subgroup Decomposition</h3>
      <p className="step-description">
        Examine how poverty varies across population subgroups. The poverty share shows
        each group's contribution to national poverty, while delta measures the difference
        from the overall M0.
      </p>

      <div className="section">
        <h4>Subgroup Results</h4>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Group</th>
                <th>N</th>
                <th>H (%)</th>
                <th>A (%)</th>
                <th>M0</th>
                <th>Pop. Share (%)</th>
                <th>Poverty Share (%)</th>
                <th>Delta</th>
              </tr>
            </thead>
            <tbody>
              {subgroups.map((sg) => (
                <tr key={sg.group_value}>
                  <td><strong>{sg.group_value}</strong></td>
                  <td>{sg.n.toLocaleString()}</td>
                  <td>{(sg.H * 100).toFixed(1)}</td>
                  <td>{(sg.A * 100).toFixed(1)}</td>
                  <td>{sg.M0.toFixed(4)}</td>
                  <td>{(sg.population_share * 100).toFixed(1)}</td>
                  <td>{(sg.poverty_share * 100).toFixed(1)}</td>
                  <td className={sg.delta > 0 ? 'text-red' : 'text-green'}>
                    {sg.delta > 0 ? '+' : ''}{sg.delta.toFixed(4)}
                  </td>
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
                x: subgroups.map((sg) => sg.group_value),
                y: subgroups.map((sg) => sg.M0),
                marker: { color: '#2563eb' },
                hovertemplate: '%{x}: M0 = %{y:.4f}<extra></extra>',
              },
            ]}
            layout={{
              title: { text: 'M0 by Subgroup' },
              yaxis: { title: { text: 'M0' } },
              xaxis: { automargin: true },
              margin: { l: 60, r: 30, t: 50, b: 80 },
              height: 400,
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
                x: subgroups.map((sg) => sg.group_value),
                y: subgroups.map((sg) => sg.poverty_share * 100),
                marker: { color: '#7c3aed' },
                hovertemplate: '%{x}: %{y:.1f}%<extra></extra>',
              },
            ]}
            layout={{
              title: { text: 'Poverty Share by Subgroup (%)' },
              yaxis: { title: { text: 'Poverty Share (%)' } },
              xaxis: { automargin: true },
              margin: { l: 60, r: 30, t: 50, b: 80 },
              height: 400,
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
