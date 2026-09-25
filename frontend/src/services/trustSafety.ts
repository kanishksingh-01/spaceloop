import { request } from './api';
import { RiskAssessment, TrustSafetyStats, EntityGraphData, ActionTaken } from '../types';

export interface AssessmentQueryParams {
  entity_type?: string;
  risk_level?: string;
  status?: string;
  limit?: number;
  offset?: number;
}

export async function getAssessments(
  params: AssessmentQueryParams = {}
): Promise<{
  success: boolean;
  total: number;
  assessments: RiskAssessment[];
}> {
  const searchParams = new URLSearchParams();
  if (params.entity_type) searchParams.set('entity_type', params.entity_type);
  if (params.risk_level) searchParams.set('risk_level', params.risk_level);
  if (params.status) searchParams.set('status', params.status);
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.offset) searchParams.set('offset', String(params.offset));

  const qs = searchParams.toString();
  return request(`/api/v1/trust-safety/assessments${qs ? `?${qs}` : ''}`);
}

export async function getAssessment(
  id: number
): Promise<{
  success: boolean;
  assessment: RiskAssessment;
}> {
  return request(`/api/v1/trust-safety/assessments/${id}`);
}

export async function takeAssessmentAction(
  id: number,
  action: ActionTaken,
  notes?: string
): Promise<{
  success: boolean;
  message: string;
  assessment: RiskAssessment;
}> {
  return request(`/api/v1/trust-safety/assessments/${id}/action`, {
    method: 'POST',
    body: JSON.stringify({ action, notes: notes || '' }),
  });
}

export async function getTrustSafetyStats(): Promise<{
  success: boolean;
  stats: TrustSafetyStats;
}> {
  return request('/api/v1/trust-safety/stats');
}

export async function getEntityGraph(
  entityType: string,
  entityId: number
): Promise<{
  success: boolean;
  entity: string;
  graph: EntityGraphData;
}> {
  return request(`/api/v1/trust-safety/graph/${entityType}/${entityId}`);
}

export async function evaluateEntity(
  entityType: string,
  entityId: number
): Promise<{
  success: boolean;
  assessment: RiskAssessment;
}> {
  return request('/api/v1/trust-safety/evaluate', {
    method: 'POST',
    body: JSON.stringify({ entity_type: entityType, entity_id: entityId }),
  });
}
