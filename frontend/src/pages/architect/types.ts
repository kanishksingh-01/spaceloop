import { LucideIcon } from 'lucide-react';

export interface SubsystemMetric {
  label: string;
  value: string;
}

export interface SubsystemSpec {
  title: string;
  codename: string;
  metric: SubsystemMetric;
  highlights: string[];
  techStack: string[];
}

export interface TeamMember {
  id: string;
  badgeNumber: string;
  name: string;
  role: string;
  domain: string;
  intro: string;
  email: string;
  linkedin: string;
  photoUrl: string;
  accent: 'cyan' | 'indigo' | 'violet' | 'amber';
  subsystem: SubsystemSpec;
}

export interface AccentThemeToken {
  color: string;
  rgb: string;
  borderLight: string;
  borderDark: string;
  text: string;
  badge: string;
  glow: string;
  icon: LucideIcon;
}
