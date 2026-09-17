export interface EvidenceCitation {
  source: string;
  url: string | null;
  claim_supported: string;
}

export interface Recommendation {
  recommendation: string;
  why_it_works: string;
  affected_metrics: string[];
  time_horizon: 'short' | 'medium' | 'long' | string;
  evidence: EvidenceCitation[];
  confidence_score: number;
  confidence_basis: string;
  constraint_notes: string | null;
  pathway_id: string;
  validation_warnings: string[];
}

export interface MissingInfoItem {
  field: string;
  category: string;
  question: string;
  priority: number;
  reason: string;
}

export interface CausalEdge {
  source: string;
  target: string;
  mechanism: string;
  confidence: string;
  evidence_corpus_ids?: string[];
}

export interface StressPathway {
  pathway_id: string;
  start_variable: string;
  terminal_variable: string;
  nodes: string[];
  edges: CausalEdge[];
  chain_length: number;
  summary: string;
  confidence: string;
}

export interface OverallConfidence {
  score: number;
  level: string;
  explanation: string;
}

export interface MetricSummary {
  field_name: string;
  value: any;
  unit: string | null;
  status: 'provided' | 'estimated' | 'unknown' | 'missing' | string;
  confidence: number | null;
  source_notes: string | null;
}

export interface ProfileSummaryResponse {
  region_name: string | null;
  biome: string | null;
  known_metrics: MetricSummary[];
  missing_metrics: string[];
  completeness_score: number;
}

export interface ActivePathwayResponse {
  pathway_id: string;
  summary: string;
  nodes: string[];
  chain_length: number;
  confidence: string;
}

export interface StructuredReportResponse {
  conversation_id: string;
  created_at: string;
  profile_summary: ProfileSummaryResponse;
  active_pathways: ActivePathwayResponse[];
  recommendations: Recommendation[];
  overall_confidence: OverallConfidence;
  narrative_summary: string;
  formatted_text: string;
}

export interface ChatResponse {
  conversation_id: string;
  turn_index: number;
  message: string;
  needs_clarification: boolean;
  missing_information: MissingInfoItem[];
  profile_summary: Record<string, any>;
  extracted_variables: Record<string, any>;
  active_stress_pathways: StressPathway[];
  retrieved_evidence: Record<string, any>[];
  recommendations: Recommendation[];
  clarification_prompt: string | null;
  report: StructuredReportResponse | null;
  formatted_text: string | null;
  narrative_summary: string | null;
  overall_confidence: OverallConfidence | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  response?: ChatResponse;
}
