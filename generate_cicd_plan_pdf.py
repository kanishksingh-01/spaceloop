#!/usr/bin/env python3
"""
SpaceLoop CI/CD Implementation Plan PDF Generator
Builds a publication-grade, multi-page architectural & DevOps specification dossier
covering GitHub Actions CI/CD Pipeline, Automated Test Matrices, and Continuous Deployment.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable, PageBreak
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for running header, footer, and dynamic total page counts."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 755, "SPACELOOP // GITHUB ACTIONS CI/CD IMPLEMENTATION PLAN")
            self.setFont("Helvetica", 8)
            self.drawRightString(612 - 40, 755, "HACK2IGNITE 2026 // DEVOPS & CI/CD BLUEPRINT")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, 748, 612 - 40, 748)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 36, 612 - 40, 36)
        
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(40, 24, "SpaceLoop — Continuous Integration & Continuous Deployment Technical Blueprint")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 40, 24, page_str)
        self.restoreState()


def create_callout(title, text, bg_hex="#F8FAFC", border_hex="#CBD5E1", title_hex="#0F172A", body_style=None):
    content = []
    if title:
        content.append(Paragraph(f"<b>{title}</b>", ParagraphStyle(
            'CalloutTitle_' + title[:10].replace(' ', '_').replace(':', ''),
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor(title_hex),
            spaceAfter=3
        )))
    content.append(Paragraph(text, body_style))
    
    t = Table([[content]], colWidths=[532])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_hex)),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor(border_hex)),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    return t


def build_cicd_pdf(filename="SpaceLoop_CICD_Implementation_Plan.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=42,
        bottomMargin=42,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    h1 = ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor("#0F172A"), spaceAfter=6)
    h2 = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=12, leading=16, textColor=colors.HexColor("#1E293B"), spaceBefore=12, spaceAfter=5)
    h3 = ParagraphStyle('H3', fontName='Helvetica-Bold', fontSize=9.5, leading=13, textColor=colors.HexColor("#334155"), spaceBefore=8, spaceAfter=3)
    body = ParagraphStyle('Body', fontName='Helvetica', fontSize=8.5, leading=12, textColor=colors.HexColor("#334155"), spaceAfter=5)
    body_bold = ParagraphStyle('BodyBold', fontName='Helvetica-Bold', fontSize=8.5, leading=12, textColor=colors.HexColor("#0F172A"))
    code_inline = ParagraphStyle('CodeInline', fontName='Courier', fontSize=7.5, leading=10, textColor=colors.HexColor("#0F172A"))
    table_cell = ParagraphStyle('TableCell', fontName='Helvetica', fontSize=8, leading=10.5, textColor=colors.HexColor("#1E293B"))
    table_header = ParagraphStyle('TableHeader', fontName='Helvetica-Bold', fontSize=8, leading=10.5, textColor=colors.white)

    story = []

    # Title Banner Block
    meta_table = Table([
        [
            Paragraph("<b>SPACELOOP CI/CD IMPLEMENTATION PLAN</b>", h1),
            Paragraph("<b>VERSION:</b> 1.0 (Production)<br/><b>DATE:</b> September 2026<br/><b>TRACK:</b> Open Innovation", table_cell)
        ],
        [
            Paragraph("Automated GitHub Actions Testing, Quality Gates & Multi-Cloud Deployment Pipeline", ParagraphStyle('Sub', fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor("#4F46E5"))),
            Paragraph("<b>TEAM:</b> LOGIC LOOP<br/><b>COLLEGE:</b> GH Raisoni ISTU, Pune", table_cell)
        ]
    ], colWidths=[370, 162])
    meta_table.setStyle(TableStyle([
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,-1), (-1,-1), 1, colors.HexColor("#4F46E5")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # Executive Summary Callout
    story.append(create_callout(
        "Executive Summary: Production Quality & Zero-Regression Automation",
        "SpaceLoop operates as a peer-to-peer micro-workspace marketplace with automated Rs. 100 UPI escrow, biometric Aadhaar tokenization, and dynamic AI matching. This document outlines the <b>GitHub Actions CI/CD Architecture</b> ensuring that all incoming commits and pull requests are automatically validated for code syntax, security policies, full frontend compilation, and zero-regression core functional audits before continuous deployment to Render and Vercel.",
        bg_hex="#EEF2FF", border_hex="#6366F1", title_hex="#312E81", body_style=body
    ))
    story.append(Spacer(1, 10))

    # Section 1: Objectives & Core Principles
    story.append(Paragraph("1. Core Pipeline Objectives & SLA Guarantees", h2))
    story.append(Paragraph(
        "The SpaceLoop CI/CD pipeline enforces four inviolable engineering pillars:",
        body
    ))

    pillars_data = [
        [
            Paragraph("<b>1. Deterministic Quality Gates</b>", body_bold),
            Paragraph("Every pull request must pass 100% of automated unit, authorization, IDOR, and security control tests before merging into <font name='Courier'>main</font>.", body)
        ],
        [
            Paragraph("<b>2. Strict Frontend Type Safety</b>", body_bold),
            Paragraph("Ensures the React 18 TypeScript codebase compiles cleanly with <font name='Courier'>tsc --noEmit</font> and Vite generates valid production assets with zero bundle drift.", body)
        ],
        [
            Paragraph("<b>3. End-to-End Functional Audit</b>", body_bold),
            Paragraph("Executes the complete 14-point functional test suite covering listing creation, AI scanning, booking lifecycle, check-in geofencing, and Rs. 100 escrow refund.", body)
        ],
        [
            Paragraph("<b>4. Automated Continuous Deployment</b>", body_bold),
            Paragraph("Triggers deployment webhooks to Render Web Service and confirms post-deployment container health and AI engine connectivity (<font name='Courier'>/api/health</font>).", body)
        ]
    ]
    t_pillars = Table(pillars_data, colWidths=[150, 382])
    t_pillars.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor("#F8FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_pillars)
    story.append(Spacer(1, 10))

    # Section 2: GitHub Actions Workflow Architecture
    story.append(Paragraph("2. GitHub Actions Pipeline Architecture (.github/workflows/ci-cd.yml)", h2))
    story.append(Paragraph(
        "The workflow triggers on pushes to <font name='Courier'>main</font>, pull requests against <font name='Courier'>main</font>, and manual <font name='Courier'>workflow_dispatch</font> runs. It executes three parallel and sequential jobs:",
        body
    ))

    jobs_data = [
        [
            Paragraph("<b>Job Identifier</b>", table_header),
            Paragraph("<b>Runtime / Environment</b>", table_header),
            Paragraph("<b>Key Execution Steps</b>", table_header),
            Paragraph("<b>Failure Policy</b>", table_header)
        ],
        [
            Paragraph("<b>backend-ci</b>", table_cell),
            Paragraph("Ubuntu Latest<br/>Python 3.11", table_cell),
            Paragraph("• Pip Cache Restore<br/>• Install <font name='Courier'>requirements.txt</font><br/>• Unit Tests (<font name='Courier'>unittest discover tests</font>)<br/>• 14-Point Functional Audit", table_cell),
            Paragraph("<b>Blocking</b><br/>PR / Push blocked on failure", table_cell)
        ],
        [
            Paragraph("<b>frontend-ci</b>", table_cell),
            Paragraph("Ubuntu Latest<br/>Node.js 20.x", table_cell),
            Paragraph("• NPM Cache Restore<br/>• Clean Install (<font name='Courier'>npm ci</font>)<br/>• TypeScript Typecheck (<font name='Courier'>tsc --noEmit</font>)<br/>• Vite Production Bundle (<font name='Courier'>npm run build</font>)", table_cell),
            Paragraph("<b>Blocking</b><br/>PR / Push blocked on failure", table_cell)
        ],
        [
            Paragraph("<b>deploy-verify</b>", table_cell),
            Paragraph("Ubuntu Latest<br/>Triggered on <font name='Courier'>main</font>", table_cell),
            Paragraph("• Runs only after CI jobs pass<br/>• Triggers Render Deploy Hook<br/>• Polls <font name='Courier'>https://spaceloop.onrender.com/api/health</font><br/>• Verifies AI Engine status online", table_cell),
            Paragraph("<b>Alerting</b><br/>Notifies deployment status", table_cell)
        ]
    ]
    t_jobs = Table(jobs_data, colWidths=[90, 105, 237, 100])
    t_jobs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E293B")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_jobs)
    
    # PageBreak to ensure Section 3 starts cleanly at the top of Page 2
    story.append(PageBreak())

    # Section 3: Test Matrix & Verification Coverage
    story.append(Paragraph("3. Automated Test Verification Matrix", h2))
    story.append(Paragraph(
        "The automated CI suite runs 43 discrete verification checks across backend and frontend:",
        body
    ))

    test_matrix = [
        [
            Paragraph("<b>Test Suite Category</b>", table_header),
            Paragraph("<b>Test Count</b>", table_header),
            Paragraph("<b>Scope & Target Subsystems</b>", table_header),
            Paragraph("<b>Expected Result</b>", table_header)
        ],
        [
            Paragraph("<b>Authentication & KYC</b>", table_cell),
            Paragraph("10 Tests", table_cell),
            Paragraph("DigiLocker Aadhaar tokenization, Discom electricity CA verification, UPI penny drop, Seeker/Host role isolation, password hashing.", table_cell),
            Paragraph("100% Pass (HTTP 200/401)", table_cell)
        ],
        [
            Paragraph("<b>Authorization & RBAC</b>", table_cell),
            Paragraph("8 Tests", table_cell),
            Paragraph("Role-based route protection, session hijacking mitigation, token revocation, host portal gating, authenticated context validation.", table_cell),
            Paragraph("100% Pass (HTTP 403)", table_cell)
        ],
        [
            Paragraph("<b>IDOR & Data Access</b>", table_cell),
            Paragraph("6 Tests", table_cell),
            Paragraph("Insecure Direct Object Reference prevention across bookings, digital access passes, personal billing data, and user profile endpoints.", table_cell),
            Paragraph("100% Pass (Zero Leakage)", table_cell)
        ],
        [
            Paragraph("<b>Security & Anti-Spoofing</b>", table_cell),
            Paragraph("5 Tests", table_cell),
            Paragraph("Rate limiting, CSP headers, XSS prevention, generic enumeration error consistency, and timing attack mitigation.", table_cell),
            Paragraph("100% Pass", table_cell)
        ],
        [
            Paragraph("<b>14-Point End-to-End Audit</b>", table_cell),
            Paragraph("14 Tests", table_cell),
            Paragraph("Full functional lifecycle: Search -> AI Match -> Listing Creation -> Instant Booking -> AI Micro-Lease -> Geofenced Check-In -> Escrow Refund.", table_cell),
            Paragraph("14/14 Operational", table_cell)
        ]
    ]
    t_matrix = Table(test_matrix, colWidths=[110, 60, 262, 100])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_matrix)
    story.append(Spacer(1, 12))

    # Section 4: Continuous Deployment (CD) Strategy
    story.append(Paragraph("4. Continuous Deployment (CD) Workflow & Rollout Strategy", h2))
    story.append(Paragraph(
        "Deployment to Render and Vercel is connected directly to the GitHub repository:",
        body
    ))

    cd_flow = [
        [
            Paragraph("<b>Phase</b>", table_header),
            Paragraph("<b>Target Platform</b>", table_header),
            Paragraph("<b>Mechanism & Configuration</b>", table_header),
            Paragraph("<b>Health Verification</b>", table_header)
        ],
        [
            Paragraph("<b>Render (WSGI API)</b>", table_cell),
            Paragraph("Render Cloud Web Service<br/>(Gunicorn + Python 3.11)", table_cell),
            Paragraph("Auto-deploys on push to <font name='Courier'>main</font> via <font name='Courier'>render.yaml</font> blueprint. Pre-built SPA assets in <font name='Courier'>public/</font> eliminate node dependency on server.", table_cell),
            Paragraph("Automated poll of <font name='Courier'>/api/health</font> with 60s timeout.", table_cell)
        ],
        [
            Paragraph("<b>Vercel (Edge SPA)</b>", table_cell),
            Paragraph("Vercel Global Edge CDN<br/>+ Serverless Functions", table_cell),
            Paragraph("Configured via <font name='Courier'>vercel.json</font>. Routes API requests to <font name='Courier'>api/index.py</font> and serves Vite SPA static assets from Edge cache.", table_cell),
            Paragraph("Edge latency check and SPA fallback routing test.", table_cell)
        ]
    ]
    t_cd = Table(cd_flow, colWidths=[95, 115, 222, 100])
    t_cd.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563EB")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_cd)
    story.append(Spacer(1, 10))

    # Section 5: Implementation Roadmap & Execution Checklist
    story.append(Paragraph("5. Step-by-Step Implementation Checklist", h2))
    
    checklist_data = [
        [
            Paragraph("<b>Step</b>", table_header),
            Paragraph("<b>Action Item</b>", table_header),
            Paragraph("<b>Verification Command / Artifact</b>", table_header),
            Paragraph("<b>Status</b>", table_header)
        ],
        [
            Paragraph("1", table_cell),
            Paragraph("Draft Implementation Plan & Architecture Dossier", table_cell),
            Paragraph("Export to <font name='Courier'>SpaceLoop_CICD_Implementation_Plan.pdf</font>", table_cell),
            Paragraph("<font color='#059669'><b>COMPLETED</b></font>", table_cell)
        ],
        [
            Paragraph("2", table_cell),
            Paragraph("Create GitHub Actions CI/CD Workflow", table_cell),
            Paragraph("Write <font name='Courier'>.github/workflows/ci-cd.yml</font> with parallel test jobs", table_cell),
            Paragraph("<font color='#2563EB'><b>READY TO EXECUTE</b></font>", table_cell)
        ],
        [
            Paragraph("3", table_cell),
            Paragraph("Add Pipeline Badges & Documentation to README", table_cell),
            Paragraph("Update <font name='Courier'>README.md</font> with GitHub Actions build status badges", table_cell),
            Paragraph("<font color='#2563EB'><b>READY TO EXECUTE</b></font>", table_cell)
        ],
        [
            Paragraph("4", table_cell),
            Paragraph("Local Test Gate Dry Run", table_cell),
            Paragraph("Execute <font name='Courier'>npm run build</font> & <font name='Courier'>python test_all_features_functional.py</font>", table_cell),
            Paragraph("<font color='#059669'><b>VERIFIED (100%)</b></font>", table_cell)
        ],
        [
            Paragraph("5", table_cell),
            Paragraph("Commit & Push to Remote Repositories", table_cell),
            Paragraph("Push to <font name='Courier'>kanishksingh-01/spaceloop</font> & <font name='Courier'>hack2ignite-practice</font>", table_cell),
            Paragraph("<font color='#2563EB'><b>READY TO PUSH</b></font>", table_cell)
        ]
    ]
    t_check = Table(checklist_data, colWidths=[30, 180, 242, 80])
    t_check.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_check)
    story.append(Spacer(1, 12))

    # Sign-off Callout
    story.append(create_callout(
        "Team Sign-off & Hack2Ignite 2026 Submission Readiness",
        "This CI/CD implementation plan guarantees industrial-grade continuous integration and continuous deployment for SpaceLoop. All components, schemas, automated tests, and deployment targets adhere strictly to the Hack2Ignite 2026 Open Innovation track standards.<br/>"
        "<b>Architect & Engineering Team:</b> Indrayani Mazumder, Kanishk Singh, Zara Quadri, Aarya Maurya.",
        bg_hex="#F0FDF4", border_hex="#22C55E", title_hex="#14532D", body_style=body
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Generated PDF: {filename} ({os.path.getsize(filename)} bytes)")


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "SpaceLoop_CICD_Implementation_Plan.pdf"
    build_cicd_pdf(out_file)
