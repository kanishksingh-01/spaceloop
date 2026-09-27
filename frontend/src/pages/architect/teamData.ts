import { Cpu, Terminal, Layers, Shield } from 'lucide-react';
import { TeamMember, AccentThemeToken } from './types';

export const TEAM_MEMBERS: TeamMember[] = [
  {
    id: 'architect-aarya',
    badgeNumber: '04',
    name: 'Aarya Maurya',
    role: 'System Architect & Security Lead',
    domain: 'Zero-Trust Boundary, DPDP Act 2023 & Fraud Prevention',
    intro:
      'Architected SpaceLoop’s zero-trust security perimeter, DPDP Act 2023 tokenized Aadhaar identity verification, and multi-tier fraud & collusion detection engine.',
    email: 'aaryamaurya.dev@gmail.com',
    linkedin: 'https://www.linkedin.com/in/aarya-maurya',
    photoUrl: '/team/aarya.jpg',
    accent: 'amber',
    subsystem: {
      title: 'Zero-Trust Defense & Multi-Tier Anomaly Engine',
      codename: 'SEC-ZERO-TRUST-SHIELD',
      metric: {
        label: 'Audit Security',
        value: '100%',
      },
      highlights: [
        'DPDP Act 2023 compliant zero-raw-storage tokenization pipeline hashing Aadhaar OTP credentials via SHA-256 salts.',
        '26-feature Isolation Forest unsupervised anomaly detection layer trained on tabular behavior metrics.',
        'Strict IDOR protection, sliding-window rate limiters, session cookie regeneration, and immutable audit telemetry.',
      ],
      techStack: ['Zero-Trust', 'Isolation Forest', 'Scikit-Learn', 'DigiLocker', 'DPDP Act 2023', 'NetworkX'],
    },
  },
  {
    id: 'architect-kanishk',
    badgeNumber: '02',
    name: 'Kanishk Singh',
    role: 'Founding Architect & Backend Lead',
    domain: 'High-Concurrency WSGI Services & Section 52 Protocol',
    intro:
      'Engineered SpaceLoop’s high-performance Flask 3.0 backend, Section 52 revocable micro-leasing protocol under the Indian Easements Act (1882), automated ₹100 UPI micro-escrow holds, and hybrid semantic search engine.',
    email: 'kanishk@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/kanishksingh01',
    photoUrl: '/team/kanishk.png',
    accent: 'indigo',
    subsystem: {
      title: 'Section 52 Engine & UPI Micro-Escrow',
      codename: 'CORE-WSGI-TRANSACT',
      metric: {
        label: 'P95 API Latency',
        value: '28ms',
      },
      highlights: [
        'Section 52 Indian Easements Act legal framework generating instant enforceable temporary space licenses.',
        'Automated ₹100 UPI micro-escrow hold protocol with instant conditional release upon GPS and QR checkout.',
        'Scalable Flask 3.0 WSGI architecture pre-configured with SQLite WAL concurrency and PostgreSQL containers.',
      ],
      techStack: ['Python 3.11', 'Flask 3.0', 'SQLAlchemy Core', 'PostgreSQL', 'UPI / NPCI API', 'Docker'],
    },
  },
  {
    id: 'architect-zara',
    badgeNumber: '03',
    name: 'Zara Quadri',
    role: 'Frontend / UI-UX Lead Developer',
    domain: 'High-Fidelity React Systems & Interactive HUDs',
    intro:
      'Crafted SpaceLoop’s responsive React 18 client architecture, Ocean Breeze light theme and Midnight Neon dark theme design systems, tactile glassmorphic controls, and mobile navigation HUD.',
    email: 'zara.quadri@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/zara-quadri',
    photoUrl: '/team/zara.jpg',
    accent: 'violet',
    subsystem: {
      title: 'Reactive Viewport & Dual-Theme System',
      codename: 'UI-REACT-VIEWPORT',
      metric: {
        label: 'Lighthouse Score',
        value: '99/100',
      },
      highlights: [
        'Zero-overflow mobile HUD interface featuring synchronized session timers, passes, and offline credentials.',
        'Dual-palette design token system powering Ocean Breeze (#0B3D91, #3BA7F2) and Midnight Neon (#020617).',
        'Interactive geospatial explore view with dynamic radius slider, category chips, and instant listing preview cards.',
      ],
      techStack: ['React 18', 'TypeScript', 'Tailwind CSS', 'Vite 5', 'Lucide Icons', 'HTML5 Canvas'],
    },
  },
  {
    id: 'architect-indrayani',
    badgeNumber: '01',
    name: 'Indrayani Mazumder',
    role: 'AI / ML & Computer Vision Specialist',
    domain: 'Multimodal Room Vision & Section 52 Matching Engine',
    intro:
      'Leads SpaceLoop’s multimodal computer vision and spatial intelligence pipeline. Architected the post-occupancy room condition delta analyzer, automatic electrical appliance off-detection, and the Groq + Gemini dual-engine intent parser.',
    email: 'indrayani@spaceloop.in',
    linkedin: 'https://www.linkedin.com/in/indrayani-mazumder',
    photoUrl: '/team/indrayani.jpg',
    accent: 'cyan',
    subsystem: {
      title: 'Multimodal Room Vision & Semantic Matcher',
      codename: 'CV-ROOM-DELTA-SCAN',
      metric: {
        label: 'Match Accuracy',
        value: '98.4%',
      },
      highlights: [
        'Multimodal room inspector analyzing acoustic dampening, ergonomics, natural lighting, and monitor availability.',
        'Post-occupancy visual delta scanner comparing check-in and check-out photos to verify zero damages.',
        'Automated computer vision edge checks confirming lights, monitors, and electrical appliances are turned off.',
      ],
      techStack: ['Python 3.11', 'OpenCV', 'Gemini 1.5 Pro', 'Groq LPU', 'PyTorch', 'NumPy'],
    },
  },
];

export const ACCENT_TOKENS: Record<TeamMember['accent'], AccentThemeToken> = {
  cyan: {
    color: '#06B6D4',
    rgb: '6, 182, 212',
    borderLight: 'border-cyan-600/30 hover:border-cyan-600',
    borderDark: 'border-cyan-500/40 hover:border-cyan-400',
    text: 'text-cyan-600 dark:text-cyan-400',
    badge: 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-300 border-cyan-500/30',
    glow: 'rgba(6, 182, 212, 0.25)',
    icon: Cpu,
  },
  indigo: {
    color: '#4F46E5',
    rgb: '79, 70, 229',
    borderLight: 'border-indigo-600/30 hover:border-indigo-600',
    borderDark: 'border-indigo-500/40 hover:border-indigo-400',
    text: 'text-indigo-600 dark:text-indigo-400',
    badge: 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-500/30',
    glow: 'rgba(79, 70, 229, 0.25)',
    icon: Terminal,
  },
  violet: {
    color: '#8B5CF6',
    rgb: '139, 92, 246',
    borderLight: 'border-violet-600/30 hover:border-violet-600',
    borderDark: 'border-violet-500/40 hover:border-violet-400',
    text: 'text-violet-600 dark:text-violet-400',
    badge: 'bg-violet-500/10 text-violet-700 dark:text-violet-300 border-violet-500/30',
    glow: 'rgba(139, 92, 246, 0.25)',
    icon: Layers,
  },
  amber: {
    color: '#F59E0B',
    rgb: '245, 158, 11',
    borderLight: 'border-amber-600/30 hover:border-amber-600',
    borderDark: 'border-amber-500/40 hover:border-amber-400',
    text: 'text-amber-600 dark:text-amber-400',
    badge: 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/30',
    glow: 'rgba(245, 158, 11, 0.25)',
    icon: Shield,
  },
};
