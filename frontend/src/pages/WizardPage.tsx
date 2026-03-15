import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/client';
import type { Project, ColumnMetadata, IndexConfiguration, AnalysisResults, RobustnessResults } from '../types';
import Step1DataUpload from '../components/wizard/Step1DataUpload';
import Step2Configuration from '../components/wizard/Step2Configuration';
import Step3Identification from '../components/wizard/Step3Identification';
import Step4Aggregation from '../components/wizard/Step4Aggregation';
import Step5DimensionalBreakdown from '../components/wizard/Step5DimensionalBreakdown';
import Step6SubgroupDecomposition from '../components/wizard/Step6SubgroupDecomposition';
import Step7Robustness from '../components/wizard/Step7Robustness';

const STEP_LABELS = [
  'Upload Data',
  'Configuration',
  'Identification',
  'Aggregation',
  'Dimensional Breakdown',
  'Subgroup Decomposition',
  'Robustness & Export',
];

export default function WizardPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const projectId = Number(id);

  const [project, setProject] = useState<Project | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [columns, setColumns] = useState<ColumnMetadata[]>([]);
  const [configuration, setConfiguration] = useState<IndexConfiguration | null>(null);
  const [results, setResults] = useState<AnalysisResults | null>(null);
  const [robustness, setRobustness] = useState<RobustnessResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadProject = async () => {
      try {
        const res = await api.get(`/projects/${projectId}`);
        setProject(res.data);
        setCurrentStep(res.data.current_step || 1);

        // Load columns if data has been uploaded
        try {
          const colRes = await api.get(`/projects/${projectId}/data/columns`);
          setColumns(colRes.data);
        } catch {
          // No data uploaded yet
        }

        // Load configuration if it exists
        try {
          const confRes = await api.get(`/projects/${projectId}/configuration`);
          setConfiguration(confRes.data);
        } catch {
          // No configuration yet
        }

        // Load results if analyzed
        if (res.data.status === 'analyzed' || res.data.status === 'complete') {
          try {
            const resultsRes = await api.get(`/projects/${projectId}/results`);
            setResults(resultsRes.data);
          } catch {
            // No results yet
          }
        }
      } catch {
        setError('Failed to load project');
      } finally {
        setLoading(false);
      }
    };
    loadProject();
  }, [projectId]);

  const goToStep = (step: number) => {
    if (step >= 1 && step <= 7) {
      setCurrentStep(step);
    }
  };

  const onColumnsLoaded = (cols: ColumnMetadata[]) => {
    setColumns(cols);
  };

  const onConfigurationSaved = (config: IndexConfiguration) => {
    setConfiguration(config);
  };

  const onResultsLoaded = (res: AnalysisResults) => {
    setResults(res);
  };

  const onRobustnessLoaded = (res: RobustnessResults) => {
    setRobustness(res);
  };

  if (loading) {
    return <div className="loading-page">Loading project...</div>;
  }

  if (error || !project) {
    return (
      <div className="error-page">
        <p>{error || 'Project not found'}</p>
        <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </div>
    );
  }

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <Step1DataUpload
            projectId={projectId}
            onColumnsLoaded={onColumnsLoaded}
          />
        );
      case 2:
        return (
          <Step2Configuration
            projectId={projectId}
            columns={columns}
            existingConfig={configuration}
            onSaved={onConfigurationSaved}
          />
        );
      case 3:
        return (
          <Step3Identification
            projectId={projectId}
            results={results}
            onResultsLoaded={onResultsLoaded}
          />
        );
      case 4:
        return (
          <Step4Aggregation results={results} />
        );
      case 5:
        return (
          <Step5DimensionalBreakdown results={results} />
        );
      case 6:
        return (
          <Step6SubgroupDecomposition
            results={results}
            hasSubgroupColumn={!!configuration?.subgroup_column}
          />
        );
      case 7:
        return (
          <Step7Robustness
            projectId={projectId}
            robustness={robustness}
            onRobustnessLoaded={onRobustnessLoaded}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="wizard-page">
      <header className="wizard-header">
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/dashboard')}>
          &larr; Dashboard
        </button>
        <h2>{project.name}</h2>
      </header>

      <div className="stepper">
        {STEP_LABELS.map((label, idx) => {
          const stepNum = idx + 1;
          return (
            <div
              key={stepNum}
              className={`stepper-item ${stepNum === currentStep ? 'active' : ''} ${stepNum < currentStep ? 'completed' : ''}`}
              onClick={() => goToStep(stepNum)}
            >
              <div className="stepper-circle">{stepNum}</div>
              <div className="stepper-label">{label}</div>
            </div>
          );
        })}
      </div>

      <div className="wizard-content">
        {renderStep()}
      </div>

      <div className="wizard-nav">
        <button
          className="btn btn-secondary"
          disabled={currentStep === 1}
          onClick={() => goToStep(currentStep - 1)}
        >
          &larr; Back
        </button>
        <span className="step-indicator">Step {currentStep} of 7</span>
        <button
          className="btn btn-primary"
          disabled={currentStep === 7}
          onClick={() => goToStep(currentStep + 1)}
        >
          Next &rarr;
        </button>
      </div>
    </div>
  );
}
