import { request } from './api';
import { CalculatorEstimate } from '../types';

export async function estimateRevenue(params: {
  space_type: string;
  square_feet: number;
  city?: string;
  amenities?: string[];
}): Promise<CalculatorEstimate> {
  return request('/api/calculator/estimate', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}
