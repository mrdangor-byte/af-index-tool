import { useState, useEffect } from 'react';
import api from '../../api/client';
import type { ColumnMetadata, IndexConfiguration, DimensionConfig, IndicatorConfig } from '../../types';

interface Props {
  projectId: number;
  columns: ColumnMetadata[];
  existingConfig: IndexConfiguration | null;
  onSaved: (config: IndexConfiguration) => void;
}

function createEmptyIndicator(): IndicatorConfig {
  return {
    name: '',
    source_column: '',
    deprivation_cutoff: 0,
    cutoff_direction: 'below',
    weight: 0,
    data_type: 'binary',
  };
}

function createEmptyDimension(): DimensionConfig {
  return {
    name: '',
    indicators: [createEmptyIndicator()],
  };
}

export default function Step2Configuration({ projectId, columns, existingConfig, onSaved }: Props) {
  const [dimensions, setDimensions] = useState<DimensionConfig[]>(
    existingConfig?.dimensions ?? [createEmptyDimension()]
  );
  const [povertyK, setPovertyK] = useState(existingConfig?.poverty_cutoff_k ?? 0.33);
  const [subgroupColumn, setSubgroupColumn] = useState(existingConfig?.subgroup_column ?? '');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (existingConfig) {
      setDimensions(existingConfig.dimensions);
      setPovertyK(existingConfig.poverty_cutoff_k);
      setSubgroupColumn(existingConfig.subgroup_column ?? '');
    }
  }, [existingConfig]);

  const totalWeight = dimensions.reduce(
    (sum, dim) => sum + dim.indicators.reduce((s, ind) => s + ind.weight, 0),
    0
  );

  const updateDimension = (dimIdx: number, field: string, value: string) => {
    setDimensions((prev) => {
      const updated = [...prev];
      updated[dimIdx] = { ...updated[dimIdx], [field]: value };
      return updated;
    });
  };

  const updateIndicator = (dimIdx: number, indIdx: number, field: string, value: string | number) => {
    setDimensions((prev) => {
      const updated = [...prev];
      const indicators = [...updated[dimIdx].indicators];
      indicators[indIdx] = { ...indicators[indIdx], [field]: value };
      updated[dimIdx] = { ...updated[dimIdx], indicators };
      return updated;
    });
  };

  const addDimension = () => {
    setDimensions((prev) => [...prev, createEmptyDimension()]);
  };

  const removeDimension = (idx: number) => {
    setDimensions((prev) => prev.filter((_, i) => i !== idx));
  };

  const addIndicator = (dimIdx: number) => {
    setDimensions((prev) => {
      const updated = [...prev];
      updated[dimIdx] = {
        ...updated[dimIdx],
        indicators: [...updated[dimIdx].indicators, createEmptyIndicator()],
      };
      return updated;
    });
  };

  const removeIndicator = (dimIdx: number, indIdx: number) => {
    setDimensions((prev) => {
      const updated = [...prev];
      updated[dimIdx] = {
        ...updated[dimIdx],
        indicators: updated[dimIdx].indicators.filter((_, i) => i !== indIdx),
      };
      return updated;
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');

    const config: IndexConfiguration = {
      poverty_cutoff_k: povertyK,
      subgroup_column: subgroupColumn || undefined,
      dimensions,
    };

    try {
      await api.post(`/projects/${projectId}/configuration`, config);
      onSaved(config);
      setSuccess('Configuration saved successfully');
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setError(axiosErr.response?.data?.detail || 'Failed to save configuration');
      } else {
        setError('Failed to save configuration');
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="step-content">
      <h3>Step 2: Configure Dimensions & Indicators</h3>
      <p className="step-description">
        Define the dimensions and indicators for your multidimensional poverty index.
        Set deprivation cutoffs, weights, and the poverty cutoff (k).
      </p>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      <div className="config-section">
        <div className="config-row">
          <div className="form-group">
            <label htmlFor="povertyK">Poverty Cutoff (k)</label>
            <input
              id="povertyK"
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={povertyK}
              onChange={(e) => setPovertyK(parseFloat(e.target.value) || 0)}
            />
            <span className="helper-text">
              A person is MPI-poor if their deprivation score is {'>='} k. Typical value: 1/3.
            </span>
          </div>
          <div className="form-group">
            <label htmlFor="subgroupCol">Subgroup Column (optional)</label>
            <select
              id="subgroupCol"
              value={subgroupColumn}
              onChange={(e) => setSubgroupColumn(e.target.value)}
            >
              <option value="">-- None --</option>
              {columns.map((col) => (
                <option key={col.name} value={col.name}>{col.name}</option>
              ))}
            </select>
            <span className="helper-text">
              Select a column to decompose results by subgroup (e.g., region, gender).
            </span>
          </div>
        </div>

        <div className="weight-summary">
          Total Weight: <strong className={Math.abs(totalWeight - 1.0) < 0.001 ? 'text-green' : 'text-red'}>
            {totalWeight.toFixed(4)}
          </strong>
          {Math.abs(totalWeight - 1.0) >= 0.001 && (
            <span className="weight-warning"> (weights should sum to 1.0)</span>
          )}
        </div>
      </div>

      {dimensions.map((dim, dimIdx) => (
        <div key={dimIdx} className="dimension-card">
          <div className="dimension-header">
            <div className="form-group">
              <label>Dimension Name</label>
              <input
                type="text"
                value={dim.name}
                onChange={(e) => updateDimension(dimIdx, 'name', e.target.value)}
                placeholder="e.g., Health, Education, Living Standards"
              />
            </div>
            <button
              className="btn btn-danger btn-sm"
              onClick={() => removeDimension(dimIdx)}
              disabled={dimensions.length === 1}
            >
              Remove Dimension
            </button>
          </div>

          <div className="indicators-list">
            {dim.indicators.map((ind, indIdx) => (
              <div key={indIdx} className="indicator-row">
                <div className="indicator-fields">
                  <div className="form-group">
                    <label>Indicator Name</label>
                    <input
                      type="text"
                      value={ind.name}
                      onChange={(e) => updateIndicator(dimIdx, indIdx, 'name', e.target.value)}
                      placeholder="e.g., Years of Schooling"
                    />
                  </div>
                  <div className="form-group">
                    <label>Source Column</label>
                    <select
                      value={ind.source_column}
                      onChange={(e) => updateIndicator(dimIdx, indIdx, 'source_column', e.target.value)}
                    >
                      <option value="">-- Select --</option>
                      {columns.map((col) => (
                        <option key={col.name} value={col.name}>{col.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Cutoff Value</label>
                    <input
                      type="number"
                      step="any"
                      value={ind.deprivation_cutoff}
                      onChange={(e) => updateIndicator(dimIdx, indIdx, 'deprivation_cutoff', parseFloat(e.target.value) || 0)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Direction</label>
                    <select
                      value={ind.cutoff_direction}
                      onChange={(e) => updateIndicator(dimIdx, indIdx, 'cutoff_direction', e.target.value)}
                    >
                      <option value="below">Below (deprived if &lt; cutoff)</option>
                      <option value="above">Above (deprived if &gt; cutoff)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Weight</label>
                    <input
                      type="number"
                      step="any"
                      min="0"
                      value={ind.weight}
                      onChange={(e) => updateIndicator(dimIdx, indIdx, 'weight', parseFloat(e.target.value) || 0)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Data Type</label>
                    <select
                      value={ind.data_type}
                      onChange={(e) => updateIndicator(dimIdx, indIdx, 'data_type', e.target.value)}
                    >
                      <option value="binary">Binary</option>
                      <option value="ordinal">Ordinal</option>
                      <option value="cardinal">Cardinal</option>
                    </select>
                  </div>
                </div>
                <button
                  className="btn btn-danger btn-sm btn-remove-indicator"
                  onClick={() => removeIndicator(dimIdx, indIdx)}
                  disabled={dim.indicators.length === 1}
                  title="Remove indicator"
                >
                  x
                </button>
              </div>
            ))}
          </div>

          <button className="btn btn-secondary btn-sm" onClick={() => addIndicator(dimIdx)}>
            + Add Indicator
          </button>
        </div>
      ))}

      <div className="config-actions">
        <button className="btn btn-secondary" onClick={addDimension}>
          + Add Dimension
        </button>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Configuration'}
        </button>
      </div>
    </div>
  );
}
