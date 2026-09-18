#!/usr/bin/env python3
"""
SpaceLoop System & Backend Architecture PDF Generator
Builds a publication-grade, multi-page architectural specification dossier
covering System Architecture, Backend Modular Architecture, Booking/Telemetry
State Machines, India Stack Zero-Hardware Protocols, and Security Boundaries.
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


class ArchitectureNumberedCanvas(canvas.Canvas):
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
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 755, "SPACELOOP // SYSTEM & BACKEND ARCHITECTURE BLUEPRINT")
            self.setFont("Helvetica", 7.5)
            self.drawRightString(612 - 40, 755, "HACK2IGNITE 2026 // TECHNICAL ARCHITECTURE DOSSIER")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(40, 748, 612 - 40, 748)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(40, 36, 612 - 40, 36)
        
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(40, 25, "SpaceLoop — AI-Powered Micro-Space Marketplace & Adaptive Micro-Leasing Platform")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 40, 25, page_str)
        self.restoreState()


def create_callout(title, text, bg_hex="#F8FAFC", border_hex="#CBD5E1", title_hex="#0F172A", body_style=None):
    content = []
    if title:
        content.append(Paragraph(f"<b>{title}</b>", ParagraphStyle(
            'CalloutTitle_' + title[:10].replace(' ', '_').replace(':', ''),
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor(title_hex),
            spaceAfter=2
        )))
    content.append(Paragraph(text, body_style))
    
    t = Table([[content]], colWidths=[532])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_hex)),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor(border_hex)),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    return t


def build_architecture_pdf(filename="SpaceLoop_System_and_Backend_Architecture.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=42,
        bottomMargin=42,
    )

    styles = getSampleStyleSheet()
    
    # Custom Brand Colors
    c_primary = colors.HexColor("#0F172A")       # Slate 900
    c_secondary = colors.HexColor("#1E293B")     # Slate 800
    c_blue = colors.HexColor("#2563EB")          # Blue 600
    c_indigo = colors.HexColor("#4F46E5")        # Indigo 600
    c_cyan = colors.HexColor("#0284C7")          # Sky 600
    c_emerald = colors.HexColor("#059669")       # Emerald 600
    c_amber = colors.HexColor("#D97706")         # Amber 600
    c_purple = colors.HexColor("#7C3AED")        # Purple 600
    c_text = colors.HexColor("#334155")          # Slate 700
    c_muted = colors.HexColor("#64748B")         # Slate 500
    c_border = colors.HexColor("#E2E8F0")        # Slate 200

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=c_primary,
        spaceAfter=2,
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_indigo,
        spaceAfter=6,
    )

    h1_style = ParagraphStyle(
        'SecH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=c_primary,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'SecH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12.5,
        textColor=c_blue,
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.2,
        textColor=c_text,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        'DocCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.25,
        leading=9.5,
        textColor=colors.HexColor("#1E293B"),
    )

    th_style = ParagraphStyle(
        'DocTH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.white,
    )

    td_style = ParagraphStyle(
        'DocTD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.25,
        leading=9.75,
        textColor=c_text,
    )

    td_bold = ParagraphStyle(
        'DocTDBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.25,
        leading=9.75,
        textColor=c_primary,
    )

    # Box styles for Diagram Nodes
    box_hdr = ParagraphStyle('BoxHdr', fontName='Helvetica-Bold', fontSize=7.5, leading=9.5, textColor=colors.white)
    box_body = ParagraphStyle('BoxBody', fontName='Helvetica', fontSize=6.75, leading=8.75, textColor=c_primary)
    box_arrow = ParagraphStyle('BoxArrow', fontName='Helvetica-Bold', fontSize=10, leading=10, alignment=1, textColor=c_indigo)

    story = []

    # =========================================================================
    # HEADER & METADATA TABLE
    # =========================================================================
    story.append(Paragraph("SpaceLoop: End-to-End System & Backend Architecture", title_style))
    story.append(Paragraph("Comprehensive Technical Specification, Component Schematics & Protocol State Machines", subtitle_style))

    meta_table = Table([
        [
            Paragraph("<b>Architecture Version:</b> 2.4.0 (Hack2Ignite 2026)", body_style),
            Paragraph("<b>Backend:</b> Python / Flask / SQLAlchemy (WAL)", body_style),
            Paragraph("<b>Frontend:</b> React 18 / Vite / Tailwind SPA", body_style),
        ],
        [
            Paragraph("<b>AI Infrastructure:</b> Dual Groq 70B + Gemini 1.5", body_style),
            Paragraph("<b>Compliance:</b> DPDP Act 2023 / Sec 52 Easements", body_style),
            Paragraph("<b>Zero-Hardware:</b> GPS 50m + OTP Handshake", body_style),
        ]
    ], colWidths=[180, 175, 177])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    # =========================================================================
    # SECTION 1: HIGH-LEVEL SYSTEM ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("1. Overall System Architecture & Data Flow", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_indigo, spaceBefore=1, spaceAfter=4))
    story.append(Paragraph(
        "SpaceLoop is structured around a decoupled, high-resilience multi-tier topology. The presentation tier consists of a modern "
        "React SPA bundled via Vite and served with dark-mode-first tokenized CSS. The API Gateway and Application Tier are powered by "
        "Flask with modular blueprints, fine-grained CORS, and SQLite WAL/PostgreSQL ORM synchronization. High-complexity spatial "
        "analytics and conversational matchmaking run on an asynchronous dual-engine AI pipeline backed by deterministic fallback algorithms.",
        body_style
    ))

    # VISUAL ARCHITECTURE FLOW DIAGRAM (Tier-by-Tier Diagram in Table Format)
    arch_diagram_data = [
        # TIER 1: CLIENT TIER
        [
            Paragraph("<b>CLIENT PRESENTATION TIER</b> (Vite React 18 SPA + Responsive Mobile/Desktop Viewports)", box_hdr),
        ],
        [
            Table([
                [
                    Paragraph("<b>Seeker Viewports</b><br/>• Micro-Space Search & Map<br/>• Conversational Matchmaker<br/>• Live Time-Slot Picker<br/>• One-Click Escrow Booking", box_body),
                    Paragraph("<b>Host Viewports</b><br/>• Multimodal AI Listing Tool<br/>• Discom Utility Verification<br/>• Dynamic Pricing Calculator<br/>• Real-time Booking Manager", box_body),
                    Paragraph("<b>In-Room Session Cockpit</b><br/>• 50m GPS Geofenced Check-in<br/>• 4-Digit Handshake PIN<br/>• Live Session Countdown<br/>• CV Exit Diff Escrow Release", box_body),
                    Paragraph("<b>LoopBot Assistant</b><br/>• AI Rental Advisor<br/>• Plaintext Sanitize Engine<br/>• Section 52 Clause Explainer<br/>• Instant Space Recommender", box_body),
                ]
            ], colWidths=[130, 130, 135, 127], style=[
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
                ('PADDING', (0,0), (-1,-1), 4),
            ])
        ],
        [Paragraph("▼ <i>HTTP/HTTPS — JSON REST Protocol & Session Authentication Cookies</i> ▼", box_arrow)],
        # TIER 2: API GATEWAY & SECURITY MIDDLEWARE
        [
            Paragraph("<b>API GATEWAY & SECURITY ENFORCEMENT TIER</b> (Flask WSGI / Gunicorn)", box_hdr),
        ],
        [
            Table([
                [
                    Paragraph("<b>CORS Policy Engine</b><br/>• Cross-Origin Isolation<br/>• Strict Allowlist Check<br/>• Credentials Included", box_body),
                    Paragraph("<b>Session & RBAC Guard</b><br/>• Flask-Login User Session<br/>• Role: Host / Seeker / Both<br/>• Unauthorized 401 JSON Handler", box_body),
                    Paragraph("<b>Rate Limiting & CSRF</b><br/>• Flask-Limiter In-Memory<br/>• Dynamic CSRF Exemption for<br/>  stateless <code>/api/*</code> endpoints", box_body),
                    Paragraph("<b>Security Headers</b><br/>• Strict-Transport-Security<br/>• X-Content-Type-Options<br/>• X-Frame-Options: DENY", box_body),
                ]
            ], colWidths=[130, 130, 135, 127], style=[
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EEF2FF")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#818CF8")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#C7D2FE")),
                ('PADDING', (0,0), (-1,-1), 4),
            ])
        ],
        [Paragraph("▼ <i>Internal Flask Blueprints & Dependency Injection</i> ▼", box_arrow)],
        # TIER 3: MODULAR REST BLUEPRINTS & DOMAIN SERVICES
        [
            Paragraph("<b>APPLICATION DOMAIN & SERVICE MODULES</b> (Modular Blueprints)", box_hdr),
        ],
        [
            Table([
                [
                    Paragraph("<b>Auth Module (v1)</b><br/>• <code>/api/v1/auth/*</code><br/>• Salted PBKDF2 Password<br/>• DPDP Aadhaar Masking<br/>• Student SSO (.ac.in)", box_body),
                    Paragraph("<b>Spaces Module (v1)</b><br/>• <code>/api/v1/spaces/*</code><br/>• Multi-Filter Geo Search<br/>• Availability Pre-Check<br/>• Dynamic Pricing Matrix", box_body),
                    Paragraph("<b>Bookings Module (v1)</b><br/>• <code>/api/v1/bookings/*</code><br/>• Conflict Detection Engine<br/>• In-Room Telemetry Flow<br/>• Micro-Lease Synthesizer", box_body),
                    Paragraph("<b>System Module (v1)</b><br/>• <code>/api/v1/system/*</code><br/>• Health & Connectivity<br/>• AI Fallback Simulator<br/>• Diagnostic Metrics", box_body),
                ]
            ], colWidths=[130, 130, 135, 127], style=[
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F0FDF4")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#4ADE80")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#BBF7D0")),
                ('PADDING', (0,0), (-1,-1), 4),
            ])
        ],
        [Paragraph("▼ <i>Asynchronous Domain Execution & External Stack Integrations</i> ▼", box_arrow)],
        # TIER 4: EXTERNAL PROTOCOLS & DATA PERSISTENCE
        [
            Paragraph("<b>EXTERNAL PROTOCOLS, DUAL-AI ENGINE & PERSISTENCE TIER</b>", box_hdr),
        ],
        [
            Table([
                [
                    Paragraph("<b>Dual-AI Fallback Engine</b><br/>• <b>Tier 1:</b> Groq Llama 3.3 70B (&lt;450ms)<br/>• <b>Tier 2:</b> Google Gemini 1.5 Flash<br/>• <b>Tier 3:</b> Deterministic Heuristics", box_body),
                    Paragraph("<b>India Stack Protocols</b><br/>• Sec 52 Easements Act (Revocable)<br/>• DigiLocker Aadhaar OTP (SHA-256)<br/>• Discom CA Meter Electricity Bill<br/>• ₹100 UPI Micro-Escrow Hold", box_body),
                    Paragraph("<b>Zero-Hardware Suite</b><br/>• Haversine GPS (50m Geofence)<br/>• 4-Digit Handshake PIN<br/>• Cryptographic Room QR Tokens<br/>• CV Condition Diff (SSIM/Diff)", box_body),
                    Paragraph("<b>Data Persistence Layer</b><br/>• SQLite WAL Mode (Busy 5000ms)<br/>• PostgreSQL Dialect-Agnostic<br/>• SQLAlchemy ORM + JSONB<br/>• Transaction Isolation", box_body),
                ]
            ], colWidths=[130, 130, 135, 127], style=[
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFBEB")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#FCD34D")),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#FDE68A")),
                ('PADDING', (0,0), (-1,-1), 4),
            ])
        ],
    ]

    t_arch = Table(arch_diagram_data, colWidths=[532])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), c_primary),
        ('BACKGROUND', (0,3), (0,3), c_indigo),
        ('BACKGROUND', (0,6), (0,6), c_emerald),
        ('BACKGROUND', (0,9), (0,9), c_amber),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 8))

    callout_1 = (
        "<b>Architectural Resilience Principle:</b> The architecture guarantees continuous operation even during external "
        "provider outages. If Groq API experiences rate limits or timeouts, requests instantaneously cascade to Google Gemini 1.5 Flash. "
        "If all external WAN connectivity is degraded, the internal deterministic offline heuristic engines handle contract generation, "
        "spatial suitability scoring, and matchmaking without crashing the booking or search workflows."
    )
    story.append(create_callout("High-Availability Fault-Tolerant AI Design", callout_1, "#EFF6FF", "#93C5FD", "#1E40AF", body_style))

    # =========================================================================
    # PAGE 2: BACKEND MODULAR ARCHITECTURE DEEP-DIVE
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("2. Backend Modular Architecture & Micro-Design", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_indigo, spaceBefore=1, spaceAfter=4))
    story.append(Paragraph(
        "The SpaceLoop backend adopts the Flask Application Factory pattern, isolating domain logic into dedicated REST blueprints, "
        "domain services, security middlewares, and dialect-agnostic ORM repositories. This design guarantees testability, strict separation "
        "of concerns, and clean API boundaries between seekers, hosts, and administrative subsystems.",
        body_style
    ))

    # BACKEND STRUCTURE BLOCK DIAGRAM
    backend_diagram_data = [
        [
            Paragraph("<b>FLASK APPLICATION FACTORY (<code>app.py:create_app()</code>)</b>", box_hdr),
            Paragraph("<b>GLOBAL CONFIGURATION & CORE EXTENSIONS</b>", box_hdr),
        ],
        [
            Paragraph(
                "• Instantiates Flask WSGI App<br/>"
                "• Registers Blueprints (<code>/api/v1/*</code>)<br/>"
                "• Serves React SPA (<code>/</code> & <code>/assets/*</code>)<br/>"
                "• Sets up Security Headers & CORS<br/>"
                "• Configures Error Handlers (401, 404, 409, 500)",
                box_body
            ),
            Paragraph(
                "• <b>Database:</b> <code>SQLAlchemy</code> with WAL pragma & busy_timeout=5000<br/>"
                "• <b>Auth Manager:</b> <code>Flask-Login</code> user loader & session store<br/>"
                "• <b>Protection:</b> <code>Flask-WTF CSRF</code> (exempts JSON API endpoints)<br/>"
                "• <b>Throttling:</b> <code>Flask-Limiter</code> rate-limiting middleware<br/>"
                "• <b>Schema Sync:</b> Cross-dialect schema column migrations",
                box_body
            ),
        ],
        [
            Paragraph("<b>MODULAR REST CONTROLLERS (<code>backend/app/api/v1/</code>)</b>", box_hdr),
            Paragraph("<b>DOMAIN SERVICES & BUSINESS LOGIC ENGINES</b>", box_hdr),
        ],
        [
            Paragraph(
                "• <b>Auth Blueprint (<code>auth.py</code>):</b> Login, Register, Logout, Me, Aadhaar OTP, Student SSO, Discom Proof.<br/>"
                "• <b>Spaces Blueprint (<code>spaces.py</code>):</b> List spaces, Create space, Detail, Check Availability, Dynamic Pricing, Inquiries.<br/>"
                "• <b>Bookings Blueprint (<code>bookings.py</code>):</b> Check conflicts, Create booking, Micro-lease contract, Geofence checkin, CV checkout, Escrow release.<br/>"
                "• <b>System Blueprint (<code>system.py</code>):</b> System health, DB stats, Dual-AI status, Simulation toggle.",
                box_body
            ),
            Paragraph(
                "• <b>AuthService:</b> Salted PBKDF2 hash, session auditing, role check.<br/>"
                "• <b>CycleLogic:</b> Booking conflict detection, overlap query calculation.<br/>"
                "• <b>SpaceAI:</b> Groq/Gemini multi-model router, spatial inspection, NLP.<br/>"
                "• <b>LeaseSynthesizer:</b> Sec 52 Easements Act revocable agreement.<br/>"
                "• <b>CVConditionDelta:</b> Entry vs Exit image comparison & appliance check.<br/>"
                "• <b>GeoEngine:</b> Haversine spherical distance calculation (50m check).",
                box_body
            ),
        ],
        [
            Paragraph("<b>DATABASE MODELS & PERSISTENCE (<code>models.py</code>)</b>", box_hdr),
            Paragraph("<b>SECURITY & PROTOCOL SAFEGUARDS (<code>security.py</code>)</b>", box_hdr),
        ],
        [
            Paragraph(
                "• <b>User:</b> Aadhaar token hash, Discom CA, Student ID, OTI score (98.5%).<br/>"
                "• <b>Space:</b> Lat/Lng, Geofence (30-50m), Keybox code, Room QR token, AI tags.<br/>"
                "• <b>Booking:</b> Session state, PIN, GPS logs, Photos, Escrow status (₹100).<br/>"
                "• <b>Review & Inquiry:</b> Ratings, AI answers, seeker/host feedback.<br/>"
                "• <b>AuditLog:</b> Action trails, client IP address, timestamp index.",
                box_body
            ),
            Paragraph(
                "• <b>Input Sanitization:</b> Bleach-based string stripping & regex cleansing.<br/>"
                "• <b>DPDP Anonymizer:</b> Aadhaar masking (<code>XXXX-XXXX-4821</code>).<br/>"
                "• <b>Escrow Guard:</b> Dual-condition cryptographic hold & release.<br/>"
                "• <b>Zero-Keybox Leakage:</b> PINs hidden until confirmed active session.<br/>"
                "• <b>Secure Headers:</b> HSTS, Content-Type-Options, Frame-Options.",
                box_body
            ),
        ],
    ]

    t_backend = Table(backend_diagram_data, colWidths=[264, 264])
    t_backend.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), c_secondary),
        ('BACKGROUND', (1,0), (1,0), c_indigo),
        ('BACKGROUND', (0,2), (0,2), c_blue),
        ('BACKGROUND', (1,2), (1,2), c_emerald),
        ('BACKGROUND', (0,4), (0,4), c_secondary),
        ('BACKGROUND', (1,4), (1,4), c_purple),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('BACKGROUND', (0,1), (0,1), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (1,1), (1,1), colors.HexColor("#EEF2FF")),
        ('BACKGROUND', (0,3), (0,3), colors.HexColor("#F0F9FF")),
        ('BACKGROUND', (1,3), (1,3), colors.HexColor("#F0FDF4")),
        ('BACKGROUND', (0,5), (0,5), colors.HexColor("#F8FAFC")),
        ('BACKGROUND', (1,5), (1,5), colors.HexColor("#FAF5FF")),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_backend)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Backend Database Concurrency & Storage Strategy", h2_style))
    story.append(Paragraph(
        "SpaceLoop implements an enterprise-grade SQLite concurrency model optimized for low overhead in dev and hackathon deployments "
        "while guaranteeing seamless migration to PostgreSQL in enterprise production: "
        "<br/>1. <b>Write-Ahead Logging (WAL):</b> Enabled via SQLite connection pragmas (<code>PRAGMA journal_mode=WAL;</code>), allowing concurrent readers and writers without lock starvation."
        "<br/>2. <b>Busy Timeout:</b> Fixed at <code>PRAGMA busy_timeout=5000;</code> to handle transient lock contention gracefully without throwing <code>sqlite3.OperationalError</code>."
        "<br/>3. <b>Synchronous NORMAL:</b> Balances durable write performance with rapid micro-transaction throughput."
        "<br/>4. <b>Dialect-Agnostic JSON:</b> Uses SQLAlchemy's generic <code>db.JSON</code>, serializing to native JSONB on PostgreSQL and JSON text on SQLite.",
        body_style
    ))

    # =========================================================================
    # PAGE 3: BOOKING & TELEMETRY STATE MACHINE
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Booking Lifecycle & In-Room Telemetry State Machine", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_indigo, spaceBefore=1, spaceAfter=4))
    story.append(Paragraph(
        "The booking subsystem implements a rigorous multi-stage state machine that guards against overbooking, enforces the Section 52 "
        "revocable license, verifies zero-hardware physical arrival via GPS geofencing, and manages the micro-escrow lifecycle.",
        body_style
    ))

    state_table_data = [
        [
            Paragraph("State Stage", th_style),
            Paragraph("Trigger & Pre-conditions", th_style),
            Paragraph("System Action & Backend Verification", th_style),
            Paragraph("Next State / Fallback", th_style),
        ],
        [
            Paragraph("<b>1. DRAFT</b><br/><font color='#64748B'>Configuring</font>", td_bold),
            Paragraph("User selects date, time window, and duration in UI.", td_style),
            Paragraph("Frontend performs <b>debounced precheck</b> against <code>/api/v1/spaces/&lt;id&gt;/check-availability</code>. No database mutation.", td_style),
            Paragraph("→ <b>AVAILABLE</b> (if slot open)<br/>→ <b>CONFLICT</b> (if overlap)", td_style),
        ],
        [
            Paragraph("<b>2. CONFLICT</b><br/><font color='#DC2626'>409 Conflict</font>", td_bold),
            Paragraph("Requested start/end time overlaps with an existing confirmed booking.", td_style),
            Paragraph("API returns HTTP 409 with <code>conflict_start</code> and <code>conflict_end</code>. UI displays contextual warning; booking button disabled.", td_style),
            Paragraph("User adjusts duration or start time → Re-triggers <b>DRAFT</b>", td_style),
        ],
        [
            Paragraph("<b>3. CONFIRMED</b><br/><font color='#059669'>Escrow Held</font>", td_bold),
            Paragraph("Available slot selected; user reviews terms and submits booking request.", td_style),
            Paragraph("1. Conflict check executes in serial transaction.<br/>2. ₹100 UPI escrow held.<br/>3. AI synthesizes Section 52 Revocable License.<br/>4. Generates unique 4-digit arrival PIN.", td_style),
            Paragraph("→ <b>AWAITING CHECK-IN</b><br/>(PIN hidden until arrival window)", td_style),
        ],
        [
            Paragraph("<b>4. CHECK-IN</b><br/><font color='#2563EB'>Zero-Hardware</font>", td_bold),
            Paragraph("Renter arrives at premises during booked time window.", td_style),
            Paragraph("1. Renter submits GPS coordinates (Haversine 50m geofence verification).<br/>2. Enters door QR token or caretaker PIN.<br/>3. Uploads optional entry room photo.", td_style),
            Paragraph("→ <b>CHECKED_IN</b> (Active)<br/>(Live session countdown active)", td_style),
        ],
        [
            Paragraph("<b>5. ACTIVE SESSION</b><br/><font color='#4F46E5'>In-Room Cockpit</font>", td_bold),
            Paragraph("Micro-lease duration in progress.", td_style),
            Paragraph("Real-time session tracker, host contact, emergency support, and on-time vacate countdown timer.", td_style),
            Paragraph("→ <b>CHECK-OUT</b><br/>(Warning at T - 15 minutes)", td_style),
        ],
        [
            Paragraph("<b>6. CHECK-OUT</b><br/><font color='#D97706'>CV Inspection</font>", td_bold),
            Paragraph("Renter concludes micro-lease and prepares to vacate space.", td_style),
            Paragraph("1. Renter uploads exit room photo.<br/>2. SpaceLoop CV compares entry vs exit photos (structural diff + lights/fan off).<br/>3. Computes Condition Match score.", td_style),
            Paragraph("→ <b>CHECKED_OUT</b><br/>(Triggers Escrow Settlement)", td_style),
        ],
        [
            Paragraph("<b>7. SETTLED</b><br/><font color='#059669'>Escrow Released</font>", td_bold),
            Paragraph("Condition match ≥85% and vacated on schedule.", td_style),
            Paragraph("₹100 UPI escrow automatically released back to renter's VPA. Objective Trust Index (OTI) updated with 100% punctuality & cleanliness.", td_style),
            Paragraph("<b>COMPLETED</b><br/>(Immutable audit log preserved)", td_style),
        ],
    ]

    t_state = Table(state_table_data, colWidths=[90, 130, 200, 112])
    t_state.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_state)
    story.append(Spacer(1, 6))

    # STATE MACHINE FLOW DIAGRAM (Horizontal Flow Pipeline)
    sm_pipeline_data = [
        [
            Paragraph("<b>[ 1. Draft Slot ]</b><br/>User configures time", box_body),
            Paragraph("►", box_arrow),
            Paragraph("<b>[ 2. Pre-Check ]</b><br/>Debounced /check API", box_body),
            Paragraph("►", box_arrow),
            Paragraph("<b>[ 3. Confirmed ]</b><br/>₹100 Escrow + Sec 52", box_body),
            Paragraph("►", box_arrow),
            Paragraph("<b>[ 4. Check-In ]</b><br/>50m GPS + OTP PIN", box_body),
            Paragraph("►", box_arrow),
            Paragraph("<b>[ 5. Check-Out ]</b><br/>CV Exit Photo Diff", box_body),
            Paragraph("►", box_arrow),
            Paragraph("<b>[ 6. Settled ]</b><br/>Auto Escrow Refund", box_body),
        ]
    ]
    t_sm_pipeline = Table(sm_pipeline_data, colWidths=[70, 14, 70, 14, 75, 14, 72, 14, 75, 14, 70], style=[
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F1F5F9")),
        ('BACKGROUND', (2,0), (2,0), colors.HexColor("#E0F2FE")),
        ('BACKGROUND', (4,0), (4,0), colors.HexColor("#EEF2FF")),
        ('BACKGROUND', (6,0), (6,0), colors.HexColor("#FEF3C7")),
        ('BACKGROUND', (8,0), (8,0), colors.HexColor("#FCE7F3")),
        ('BACKGROUND', (10,0), (10,0), colors.HexColor("#DCFCE7")),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3),
    ])
    story.append(t_sm_pipeline)
    story.append(Spacer(1, 6))

    callout_conflict = (
        "<b>Architectural Bug Fix Reflection (Conflict Lifecycle):</b> Previously, the booking interface triggered a premature "
        "'Booking Conflict' banner before parameter selection was finalized. The architecture now enforces a clean state separation: "
        "the booking engine only queries availability once valid start/end timestamps are supplied (debounced at 350ms), clears stale "
        "conflict errors immediately on input change, and guarantees that 409 responses provide structured conflict intervals."
    )
    story.append(create_callout("Resolution of Transient Booking Conflicts", callout_conflict, "#FEF2F2", "#FECACA", "#991B1B", body_style))

    # =========================================================================
    # PAGE 4: INDIA STACK & ZERO-HARDWARE PROTOCOLS
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4. India Stack Integration & Zero-Hardware Suite", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_indigo, spaceBefore=1, spaceAfter=4))
    story.append(Paragraph(
        "SpaceLoop is custom-engineered for the Indian regulatory and urban environment. Traditional smart locks are prohibitively "
        "expensive (₹15,000+ CapEx per door) and prone to Wi-Fi disconnects. SpaceLoop eliminates all physical hardware requirements "
        "via mathematical GPS geofencing, encrypted door tokens, and India Stack digital public goods.",
        body_style
    ))

    india_stack_data = [
        [
            Paragraph("Protocol / Layer", th_style),
            Paragraph("Statutory / Technical Standard", th_style),
            Paragraph("Cryptographic & Algorithmic Implementation", th_style),
            Paragraph("Platform Impact", th_style),
        ],
        [
            Paragraph("<b>Legal Tenancy Defense</b>", td_bold),
            Paragraph("Section 52, Indian Easements Act (1882)", td_style),
            Paragraph("AI Micro-Lease Synthesizer auto-generates a <b>pure revocable license</b> specifying hour-by-hour access, explicit exclusion of tenant rights, and immediate revocation on violation.", td_style),
            Paragraph("Zero statutory tenancy risk; host retains 100% legal possession.", td_style),
        ],
        [
            Paragraph("<b>DigiLocker KYC</b>", td_bold),
            Paragraph("DPDP Act 2023 Compliant Identity", td_style),
            Paragraph("Simulated Aadhaar OTP generates a <b>Salted SHA-256 hash</b> (<code>aadhaar_token_hash</code>). Raw 12-digit UID is never persisted; client UI displays masked <code>XXXX-XXXX-4821</code>.", td_style),
            Paragraph("100% DPDP compliance with zero raw Aadhaar liability.", td_style),
        ],
        [
            Paragraph("<b>Host Utility Proof</b>", td_bold),
            Paragraph("BBPS / State Discom Consumer Account", td_style),
            Paragraph("Hosts link power meter Consumer Account (CA) number (BESCOM, TPDDL, Tata Power, etc.). Validates physical control and operational electricity grid connection.", td_style),
            Paragraph("Eliminates fraudulent and non-existent host listings.", td_style),
        ],
        [
            Paragraph("<b>Student Access SSO</b>", td_bold),
            Paragraph("University Domain Verification", td_style),
            Paragraph("Validates enrolled student credentials via institutional email domains (<code>.ac.in</code> / <code>.edu.in</code>). Student ID card numbers are masked and hashed.", td_style),
            Paragraph("Unlocks subsidized hourly study/project rates for youth.", td_style),
        ],
        [
            Paragraph("<b>Micro-Escrow Hold</b>", td_bold),
            Paragraph("UPI 2.0 Mandate / Pre-auth Emulation", td_style),
            Paragraph("Pre-authorizes a ₹100 micro-security deposit at booking confirmation. Deposit remains frozen in escrow until CV exit condition diff verifies clean departure.", td_style),
            Paragraph("Protects host furniture without heavy renter cash locks.", td_style),
        ],
        [
            Paragraph("<b>Zero-Hardware Arrival</b>", td_bold),
            Paragraph("Haversine Spherical Distance Algorithm", td_style),
            Paragraph("<code>d = 2r × arcsin(√(sin²(Δlat/2) + cos(lat1)cos(lat2)sin²(Δlng/2)))</code><br/>Enforces a strict <b>50-meter radius</b> boundary before check-in is unlocked.", td_style),
            Paragraph("₹0 Host CapEx; prevents remote fraudulent check-ins.", td_style),
        ],
    ]

    t_india = Table(india_stack_data, colWidths=[95, 110, 215, 112])
    t_india.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 3.5),
    ]))
    story.append(t_india)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Objective Telemetry & Trust Index (OTI) Formula", h2_style))
    story.append(Paragraph(
        "Instead of subjective, biased 5-star star reviews, SpaceLoop computes an immutable <b>Objective Telemetry & Trust Index (OTI)</b> "
        "grounded in verified in-room session behavior: "
        "<br/><code><b>OTI = (0.35 × Punctuality) + (0.35 × CleanlinessMatch) + (0.20 × IdentityTrust) + (0.10 × DisputeRate)</b></code>"
        "<br/>• <b>Punctuality (35%):</b> Measures on-time departure within the micro-lease window based on GPS check-out timestamp."
        "<br/>• <b>Cleanliness & Condition Match (35%):</b> Computer Vision delta comparing entry vs exit photos (verifying lights/fans off, furniture unchanged)."
        "<br/>• <b>Identity Trust (20%):</b> Verification tier achieved (Aadhaar, Student SSO, Discom power bill)."
        "<br/>• <b>Dispute History (10%):</b> Ratio of completed bookings with zero damage claims or deposit forfeitures.",
        body_style
    ))

    # =========================================================================
    # PAGE 5: DUAL-AI ENGINE & API ROUTING MATRIX
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("5. Dual-AI Fallback Engine & Routing Security Matrix", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=c_indigo, spaceBefore=1, spaceAfter=4))
    story.append(Paragraph(
        "SpaceLoop deploys a high-throughput dual-AI architecture capable of sub-second inference while guaranteeing 100% platform uptime "
        "through deterministic offline heuristics. All endpoints are guarded by security middleware and role-based access control.",
        body_style
    ))

    # AI FLOW DIAGRAM
    ai_diagram_data = [
        [
            Paragraph("<b>REQUEST INGESTION</b><br/>Multimodal Space Inspection, Listing Copy, Conversational Query, LoopBot Chat, or Condition Diff", box_hdr),
        ],
        [
            Table([
                [
                    Paragraph("<b>TIER 1: Primary Inference (Groq Cloud)</b><br/>• Model: <code>openai/gpt-oss-120b</code> & <code>gpt-oss-20b</code><br/>• Latency: &lt;450ms | Format: Strict JSON Mode<br/>• Tasks: Listing copy, spatial dimension extraction, conversational matching", box_body),
                    Paragraph("<b>TIER 2: Multimodal Failover (Google Gemini)</b><br/>• Model: <code>gemini-1.5-flash</code> / <code>gemini-3.8-flash</code><br/>• Triggers on Groq 429/500/Timeout<br/>• Tasks: Complex visual inspection, OCR contract extraction", box_body),
                    Paragraph("<b>TIER 3: Deterministic Offline Heuristics</b><br/>• Engine: Built-in Python rule-based algorithms<br/>• Zero external network dependency<br/>• Guarantees 100% uptime in air-gapped scenarios", box_body),
                ]
            ], colWidths=[175, 175, 174], style=[
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
                ('BOX', (0,0), (-1,-1), 0.5, c_border),
                ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
                ('PADDING', (0,0), (-1,-1), 4),
            ])
        ],
        [
            Paragraph("<b>LOOPBOT OUTPUT SANITIZATION ENGINE (<code>space_ai.py:_clean_loopbot_output</code>)</b>", box_hdr),
        ],
        [
            Paragraph(
                "Ensures AI assistant responses are crisp, readable, and free of noisy raw markdown. Statically strips markdown table fences "
                "(<code>| Header |</code>), HTML line breaks (<code>&lt;br&gt;</code>), and excessive formatting. Client UI renders "
                "sanitized bulleted plaintext with bullet points and bold section headers with <code>overflow-wrap: anywhere; word-break: break-word;</code>.",
                box_body
            ),
        ]
    ]
    t_ai = Table(ai_diagram_data, colWidths=[532], style=[
        ('BACKGROUND', (0,0), (0,0), c_primary),
        ('BACKGROUND', (0,2), (0,2), c_indigo),
        ('PADDING', (0,0), (-1,-1), 2),
    ])
    story.append(t_ai)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Core API Routing Matrix & Security Boundaries", h2_style))
    api_matrix_data = [
        [
            Paragraph("HTTP Method & Route", th_style),
            Paragraph("Blueprint", th_style),
            Paragraph("Auth & RBAC", th_style),
            Paragraph("Domain Responsibility & Output", th_style),
        ],
        [
            Paragraph("<code>POST /api/v1/auth/login</code>", code_style),
            Paragraph("api_v1_auth", td_style),
            Paragraph("Public / Anonymous", td_style),
            Paragraph("Authenticates user via email/password; creates session cookie.", td_style),
        ],
        [
            Paragraph("<code>GET  /api/v1/auth/me</code>", code_style),
            Paragraph("api_v1_auth", td_style),
            Paragraph("Authenticated", td_style),
            Paragraph("Returns active user profile, verification status, and OTI score.", td_style),
        ],
        [
            Paragraph("<code>POST /api/v1/auth/verify-aadhaar</code>", code_style),
            Paragraph("api_v1_auth", td_style),
            Paragraph("Authenticated", td_style),
            Paragraph("Validates Aadhaar OTP; saves salted SHA-256 hash; returns masked UID.", td_style),
        ],
        [
            Paragraph("<code>GET  /api/v1/spaces</code>", code_style),
            Paragraph("api_v1_spaces", td_style),
            Paragraph("Public", td_style),
            Paragraph("Searches active spaces by category, city, price, and coordinates.", td_style),
        ],
        [
            Paragraph("<code>GET  /api/v1/spaces/&lt;id&gt;</code>", code_style),
            Paragraph("api_v1_spaces", td_style),
            Paragraph("Public", td_style),
            Paragraph("Returns space details, AI attributes, host trust badges, and reviews.", td_style),
        ],
        [
            Paragraph("<code>GET  /api/v1/spaces/&lt;id&gt;/check-availability</code>", code_style),
            Paragraph("api_v1_spaces", td_style),
            Paragraph("Public", td_style),
            Paragraph("Debounced precheck for slot overlap; returns 200 or 409 conflict intervals.", td_style),
        ],
        [
            Paragraph("<code>POST /api/v1/bookings</code>", code_style),
            Paragraph("api_v1_bookings", td_style),
            Paragraph("Seeker / Host / Admin", td_style),
            Paragraph("Creates confirmed booking; holds ₹100 escrow; generates Section 52 license.", td_style),
        ],
        [
            Paragraph("<code>POST /api/v1/bookings/&lt;id&gt;/checkin</code>", code_style),
            Paragraph("api_v1_bookings", td_style),
            Paragraph("Booking Renter", td_style),
            Paragraph("Verifies 50m GPS geofence + PIN handshake; starts active session.", td_style),
        ],
        [
            Paragraph("<code>POST /api/v1/bookings/&lt;id&gt;/checkout</code>", code_style),
            Paragraph("api_v1_bookings", td_style),
            Paragraph("Booking Renter", td_style),
            Paragraph("Uploads exit photo; runs CV condition diff; settles and releases escrow.", td_style),
        ],
        [
            Paragraph("<code>POST /api/v1/spaces/chatbot</code>", code_style),
            Paragraph("api_v1_spaces", td_style),
            Paragraph("Public", td_style),
            Paragraph("Routes conversational renter inquiries to sanitized LoopBot AI engine.", td_style),
        ],
        [
            Paragraph("<code>GET  /api/v1/system/health</code>", code_style),
            Paragraph("api_v1_system", td_style),
            Paragraph("Public", td_style),
            Paragraph("System health probe: DB connectivity, dual-AI status, and uptime.", td_style),
        ],
    ]

    t_api = Table(api_matrix_data, colWidths=[150, 75, 95, 212])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_api)
    story.append(Spacer(1, 6))

    # =========================================================================
    # SUMMARY CALLOUT / CONCLUSION
    # =========================================================================
    summary_callout = (
        "<b>Architectural Production Readiness:</b> The SpaceLoop platform architecture completely fulfills the demands of modern "
        "urban micro-leasing. By fusing the <b>Section 52 Revocable License</b> with <b>zero-hardware GPS geofencing</b>, "
        "<b>DigiLocker DPDP-compliant verification</b>, and a <b>sub-second dual-AI engine</b>, SpaceLoop delivers an uncompromised, "
        "secure, and scalable system ready for production deployment."
    )
    story.append(create_callout("SpaceLoop Architectural Sign-Off", summary_callout, "#F0FDF4", "#86EFAC", "#15803D", body_style))

    # Build Document
    doc.build(story, canvasmaker=ArchitectureNumberedCanvas)
    print(f"Architecture PDF successfully generated: {os.path.abspath(filename)}")
    return os.path.abspath(filename)


if __name__ == "__main__":
    output_pdf = sys.argv[1] if len(sys.argv) > 1 else "SpaceLoop_System_and_Backend_Architecture.pdf"
    build_architecture_pdf(output_pdf)
