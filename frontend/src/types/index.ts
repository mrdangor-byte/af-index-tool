export interface User {
  id: number;
  email: string;
  full_name: string;
  institution?: string;
}

export interface Project {
  id: number;
  name: string;
  description?: string;
  status: 'draft' | 'configured' | 'analyzed' | 'complete';
  current_step: number;
  created_at: string;
}

export interface ColumnMetadata {
  name: string;
  dtype: string;
  missing_count: number;
  unique_count: number;
  min?: number;
  max?: number;
  mean?: number;
}

export interface IndicatorConfig {
  name: string;
  source_column: string;
  deprivation_cutoff: number;
  cutoff_direction: 'below' | 'above';
  weight: number;
  data_type: 'binary' | 'ordinal' | 'cardinal';
}

export interface DimensionConfig {
  name: string;
  indicators: IndicatorConfig[];
}

export interface IndexConfiguration {
  poverty_cutoff_k: number;
  subgroup_column?: string;
  dimensions: DimensionConfig[];
}

export interface HeadlineResults {
  H: number;
  A: number;
  M0: number;
  q: number;
  n: number;
}

export interface DimensionalBreakdown {
  indicator_name: string;
  dimension: string;
  weight: number;
  censored_headcount: number;
  raw_headcount: number;
  contribution: number;
  absolute_contribution: number;
}

export interface SubgroupResult {
  group_value: string;
  n: number;
  q: number;
  H: number;
  A: number;
  M0: number;
  population_share: number;
  poverty_share: number;
  delta: number;
}

export interface AnalysisResults {
  headline: HeadlineResults;
  dimensional_breakdown: DimensionalBreakdown[];
  subgroup_decomposition?: SubgroupResult[];
}

export interface RobustnessResults {
  k_robustness: Array<{ k: number; H: number; A: number; M0: number; q: number }>;
  weight_robustness?: Array<{ scenario: number; weights: number[]; H: number; A: number; M0: number }>;
  leave_one_out?: Array<{ dropped_indicator: string; H: number; A: number; M0: number }>;
}
