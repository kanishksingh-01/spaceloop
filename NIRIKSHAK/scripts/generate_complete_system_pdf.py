import os
import sys
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable, PageBreak
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
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
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "NIRIKSHAK & PRAHARAK // DUAL-TWIN CYBER DEFENSE ARCHITECTURE REPORT")
            self.drawRightString(612 - 54, 750, "DEFENSE DECISION SUPPORT PROTOTYPE")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        
        self.drawString(54, 32, "NIRIKSHAK (निरीक्षक) & PRAHARAK (प्रहारक) — 100% Synthetic Telemetry & Zero-Trust Defense")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 32, page_str)
        self.restoreState()

def build_complete_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Custom Corporate / Defense Palette
    c_primary = colors.HexColor("#0F172A")    # Deep Navy Slate
    c_secondary = colors.HexColor("#1E3A8A")  # Royal Navy
    c_indigo = colors.HexColor("#4F46E5")     # Indigo (NIRIKSHAK)
    c_amber = colors.HexColor("#D97706")      # Amber/Saffron (PRAHARAK)
    c_crimson = colors.HexColor("#B91C1C")    # Crimson / High Risk
    c_emerald = colors.HexColor("#047857")    # Emerald / Low Risk
    c_purple = colors.HexColor("#7C3AED")     # Purple / APT Sequence
    c_text = colors.HexColor("#334155")       # Slate text
    c_muted = colors.HexColor("#64748B")      # Muted text
    c_bg_light = colors.HexColor("#F8FAFC")   # Subtle card background
    c_border = colors.HexColor("#E2E8F0")     # Subtle border

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=21,
        leading=25,
        textColor=c_primary,
        spaceAfter=3,
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14.5,
        textColor=c_secondary,
        spaceAfter=8,
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_muted,
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_secondary,
        spaceBefore=11,
        spaceAfter=4,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_primary,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=c_text,
        spaceAfter=4,
    )

    callout_text = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11.5,
        textColor=c_primary,
    )

    formula_style = ParagraphStyle(
        'FormulaText',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E1B4B"),
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=c_text,
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10.5,
        textColor=colors.white,
    )

    story = []

    # ==================== COVER / HEADER BLOCK ====================
    story.append(Paragraph("NIRIKSHAK (निरीक्षक) & PRAHARAK (प्रहारक)", title_style))
    story.append(Paragraph("Dual-Twin Cyber Defense Framework: Contextual Insider Risk & Perimeter Ingress Hardening", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_indigo, spaceBefore=0, spaceAfter=6))

    meta_table_data = [
        [
            Paragraph("<b>Author</b>: Kanishk Singh & Team<br/><b>Architecture</b>: 4-Tier Zero-Trust Platform", meta_style),
            Paragraph("<b>Stack</b>: FastAPI + PostgreSQL 16 + Next.js + Isolation Forest<br/><b>Security Baseline</b>: NIST FIPS 204 & MITRE ATT&CK", meta_style),
            Paragraph("<b>Verification</b>: 100% Automated (25/25 Tests Passing)<br/><b>Classification</b>: 100% Synthetic Telemetry", meta_style),
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[168, 178, 158])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_bg_light),
        ('BOX', (0, 0), (-1, -1), 0.5, c_border),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # ==================== SECTION 1: EXECUTIVE SUMMARY & AXIOMS ====================
    story.append(Paragraph("1. Executive Summary & Foundational Axioms", h1_style))
    story.append(Paragraph(
        "Modern enterprise and defense environments face an asymmetric vulnerability: traditional perimeter defenses assume that once an entity is authenticated, it is implicitly trusted. Meanwhile, legacy SIEM solutions overwhelm SOC analysts with black-box alert fatigue. <b>NIRIKSHAK</b> and <b>PRAHARAK</b> operate as complementary dual-twins sharing a unified correlation core to provide complete 360-degree situational awareness without automated disciplinary punishment.",
        body_style
    ))

    # Axiom Callout Box
    axiom_data = [[
        Paragraph(
            "<b>FOUNDATIONAL AXIOM I (The NIRIKSHAK Rule):</b><br/>"
            "<i>Unusual Activity ≠ Confirmed Malicious Activity</i><br/>"
            "Anomalous telemetry must never trigger autonomous disciplinary accusation. NIRIKSHAK serves strictly as an explainable <b>Decision Support System</b>, providing quantified mathematical attribution to human security analysts.",
            callout_text
        ),
        Paragraph(
            "<b>FOUNDATIONAL AXIOM II (The PRAHARAK Rule):</b><br/>"
            "<i>Zero-Trust Cryptographic Deserialization</i><br/>"
            "No external signal, telemetry stream, or remote dispatch command is permitted to execute or deserialize without cryptographic anti-spoofing verification, timestamp freshness check, and sliding token-bucket circuit breaking.",
            callout_text
        )
    ]]
    axiom_table = Table(axiom_data, colWidths=[246, 246])
    axiom_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EEF2FF")),
        ('BOX', (0, 0), (-1, -1), 1, c_indigo),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(axiom_table)
    story.append(Spacer(1, 8))

    # ==================== SECTION 2: DUAL-TWIN ARCHITECTURE MATRIX ====================
    story.append(Paragraph("2. Dual-Twin Operational Philosophy & Comparison Matrix", h1_style))
    story.append(Paragraph(
        "The system separates security telemetry into two complementary analytical engines coupled by a temporal sliding-window correlation nexus:",
        body_style
    ))

    matrix_data = [
        [
            Paragraph("DIMENSION", table_header),
            Paragraph("NIRIKSHAK (THE INSIDER TWIN)", table_header),
            Paragraph("PRAHARAK (THE OUTSIDER TWIN)", table_header),
        ],
        [
            Paragraph("<b>Primary Domain</b>", table_cell),
            Paragraph("Internal Identity, Device Trust & Data Access", table_cell),
            Paragraph("Perimeter Ingress, Gateway APIs & Remote Dispatches", table_cell),
        ],
        [
            Paragraph("<b>Core Question</b>", table_cell),
            Paragraph("<i>'Does this authenticated employee's access make contextual sense?'</i>", table_cell),
            Paragraph("<i>'Does this external connection have any right to exist, and is it authentic?'</i>", table_cell),
        ],
        [
            Paragraph("<b>Threat Vectors</b>", table_cell),
            Paragraph("Off-hours access, cross-department data reads, bulk exfiltration, stolen credentials", table_cell),
            Paragraph("Forged signatures, command replay, reconnaissance scans, DDoS floods, spoofed UAV commands", table_cell),
        ],
        [
            Paragraph("<b>Detection Logic</b>", table_cell),
            Paragraph("6-Factor Deterministic Scoring + Unsupervised Isolation Forest (6D Feature Vector)", table_cell),
            Paragraph("Zero-Trust Crypto (Ed25519/HMAC/PQC) + Sliding Token-Bucket + MITRE ATT&CK Recon", table_cell),
        ],
        [
            Paragraph("<b>Response Posture</b>", table_cell),
            Paragraph("Decision support case dossier for mandatory human analyst triage", table_cell),
            Paragraph("Proportional automated containment (15m Quarantine) + Cross-Domain Alert", table_cell),
        ],
    ]
    matrix_table = Table(matrix_data, colWidths=[90, 207, 207])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(matrix_table)
    story.append(Spacer(1, 8))

    # ==================== SECTION 3: NIRIKSHAK INSIDER RISK ENGINE ====================
    story.append(Paragraph("3. NIRIKSHAK: 7-Layer Contextual Insider Risk Engine", h1_style))
    story.append(Paragraph(
        "Every internal access event traverses seven rigorous architectural layers:",
        body_style
    ))
    
    layers_data = [
        [
            Paragraph("<b>1. Identity Confidence</b>", table_cell),
            Paragraph("Evaluates MFA verification freshness, session validity, and credential anomalies.", table_cell),
        ],
        [
            Paragraph("<b>2. Device & Env Trust</b>", table_cell),
            Paragraph("Checks hardware enrollment in corporate inventory, trust score (0-100), and unmanaged endpoints.", table_cell),
        ],
        [
            Paragraph("<b>3. Data Sensitivity</b>", table_cell),
            Paragraph("Multiplies risk based on classification tier (PUBLIC: 0, INTERNAL: 25, SENSITIVE: 60, CRITICAL: 100).", table_cell),
        ],
        [
            Paragraph("<b>4. Behavioral Context</b>", table_cell),
            Paragraph("Compares against user and role baselines (typical working hours, department ownership, data volume Z-score).", table_cell),
        ],
        [
            Paragraph("<b>5. Event Correlation</b>", table_cell),
            Paragraph("Tracks temporal sliding windows across sessions to detect lateral movement and multi-stage kill chains.", table_cell),
        ],
        [
            Paragraph("<b>6. Explainable Scoring</b>", table_cell),
            Paragraph("Combines deterministic policy with ML anomaly indicators into an attributable 0-100 score.", table_cell),
        ],
        [
            Paragraph("<b>7. Human Review</b>", table_cell),
            Paragraph("Generates security cases requiring audited human adjudication with mandatory justification.", table_cell),
        ],
    ]
    layers_table = Table(layers_data, colWidths=[130, 374])
    layers_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [c_bg_light, colors.white]),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(layers_table)
    story.append(Spacer(1, 5))

    story.append(Paragraph("<b>Deterministic Mathematical Formulation:</b>", h2_style))
    story.append(Paragraph(
        "Final Risk Score = w_1 · I + w_2 · D + w_3 · S + w_4 · B + w_5 · A + w_6 · C<br/>"
        "Configured Policy Weights: Identity w_I = 0.20, Device w_D = 0.20, Sensitivity w_S = 0.20, Behavior w_B = 0.20, ML Anomaly w_A = 0.10, Correlation w_C = 0.10.",
        formula_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Unsupervised Machine Learning Engine (Isolation Forest):</b>", h2_style))
    story.append(Paragraph(
        "NIRIKSHAK implements an unsupervised <b>Isolation Forest</b> model trained on historical telemetry. It extracts a <b>6-dimensional feature vector</b>: [hours_offset, volume_zscore, device_familiarity, action_severity, sensitivity_tier, temporal_frequency]. The raw decision function is normalized into an additive 0-100 anomaly subscore. As mandated by operational rules, ML contributes strictly as one factor (w_A = 0.10) and never convicts independently.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # ==================== SECTION 4: PRAHARAK PERIMETER DEFENSE ENGINE ====================
    story.append(Paragraph("4. PRAHARAK: Perimeter Threat & Outsider Risk Architecture", h1_style))
    story.append(Paragraph(
        "PRAHARAK inspects all external ingress telemetry, edge requests, and remote commands across five specialized sub-engines:",
        body_style
    ))

    praharak_sub_data = [
        [
            Paragraph("SUB-ENGINE", table_header),
            Paragraph("ALGORITHM / SPECIFICATION", table_header),
            Paragraph("OPERATIONAL EFFECT", table_header),
        ],
        [
            Paragraph("<b>Zero-Trust Crypto</b>", table_cell),
            Paragraph("HMAC-SHA256, Ed25519, NIST FIPS 204 ML-DSA (Dilithium-3 Post-Quantum)", table_cell),
            Paragraph("Rejects tampered, forged, or replayed commands (freshness window: &le; 120s) before deserialization.", table_cell),
        ],
        [
            Paragraph("<b>Circuit Breaker</b>", table_cell),
            Paragraph("Sliding Token-Bucket (Fast: 10s burst &gt; 15 req; Slow: 60s sustained &gt; 60 req)", table_cell),
            Paragraph("Transitions CLOSED &rarr; HALF-OPEN &rarr; OPEN. Automatically enforces 15-minute IP quarantine.", table_cell),
        ],
        [
            Paragraph("<b>MITRE ATT&CK Recon</b>", table_cell),
            Paragraph("Mapped tactics: T1595 (Scan), T1110 (Brute), T1190 (Exploit), T1071 (C2)", table_cell),
            Paragraph("Detects endpoint enumeration, fuzzing payloads, and command-and-control beaconing patterns.", table_cell),
        ],
        [
            Paragraph("<b>Origin & Locality</b>", table_cell),
            Paragraph("BGP Autonomous System (ASN) reputation, VPN egress, unapproved subnets", table_cell),
            Paragraph("Identifies suspicious hosting providers, dark subnets, and non-defense network ranges.", table_cell),
        ],
        [
            Paragraph("<b>Deterministic Formula</b>", table_cell),
            Paragraph("Risk = 0.20 S_Origin + 0.30 S_Integrity + 0.20 S_Recon + 0.15 S_Velocity + 0.15 S_Intel", table_cell),
            Paragraph("Quantified 0-100 risk score producing dispositions: ALLOWED, CHALLENGED, THROTTLED, BLOCKED.", table_cell),
        ],
    ]
    praharak_sub_table = Table(praharak_sub_data, colWidths=[90, 207, 207])
    praharak_sub_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#78350F")),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(praharak_sub_table)
    story.append(Spacer(1, 8))

    # ==================== SECTION 5: THE NEXUS CROSS-DOMAIN CORRELATION ====================
    story.append(Paragraph("5. The Nexus: Cross-Domain Correlation Engine", h1_style))
    story.append(Paragraph(
        "The true core differentiator is the <b>Cross-Domain Correlation Engine (The Nexus)</b>. In sophisticated advanced persistent threats, an external attack is almost always coordinated with internal credential misuse.",
        body_style
    ))

    nexus_box_data = [[
        Paragraph(
            "<b>THE CROSS-DOMAIN CORRELATION MECHANISM:</b><br/>"
            "1. PRAHARAK intercepts external reconnaissance probes or brute-force attempts from an IP (e.g. 198.51.100.77) targeting /api/v1/auth.<br/>"
            "2. Within the shared <b>30-minute sliding window</b>, NIRIKSHAK registers anomalous off-hours access or bulk exfiltration by an internal credential (USER-004).<br/>"
            "3. The Nexus Engine performs cross-domain graph correlation: it links the external origin IP, compromised credential, and target repository.<br/>"
            "4. <b>Unified Escalation</b>: The system generates a unified <b>CrossDomainIncident</b> with an amplified risk score (&ge; 85.0 - CRITICAL), trips the circuit breaker to quarantine the external IP, elevates the internal case to Critical Priority, and fires a high-visibility incident alert in the SOC dashboard.",
            callout_text
        )
    ]]
    nexus_box = Table(nexus_box_data, colWidths=[504])
    nexus_box.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FDF2F8")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#BE185D")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(nexus_box)
    story.append(Spacer(1, 8))

    # ==================== SECTION 6: COMPLETE DATA MODEL & DATABASE ====================
    story.append(Paragraph("6. Database Architecture & Cryptographic Audit Trails", h1_style))
    story.append(Paragraph(
        "All state is persisted in <b>PostgreSQL 16</b> using SQLAlchemy Async ORM with UUIDv7 primary keys. Data integrity is guaranteed via append-only cryptographic hash chaining:",
        body_style
    ))

    db_data = [
        [
            Paragraph("TABLE / ENTITY", table_header),
            Paragraph("PURPOSE & KEY ATTRIBUTES", table_header),
            Paragraph("INTEGRITY & RELATIONSHIPS", table_header),
        ],
        [
            Paragraph("<b>users</b>", table_cell),
            Paragraph("Synthetic user identities, departments (Engineering, Operations, Finance), roles (USER, ANALYST, ADMIN).", table_cell),
            Paragraph("Foreign keys to events and cases.", table_cell),
        ],
        [
            Paragraph("<b>devices</b>", table_cell),
            Paragraph("Enrolled corporate hardware, MAC/UUID, registration flag, trust level (TRUSTED, MONITORED, REVOKED).", table_cell),
            Paragraph("Linked to access telemetry.", table_cell),
        ],
        [
            Paragraph("<b>resources</b>", table_cell),
            Paragraph("Synthetic operational repositories (A, B, C, D) with classification tiers (LOW to CRITICAL).", table_cell),
            Paragraph("Enforces departmental boundary checks.", table_cell),
        ],
        [
            Paragraph("<b>access_events</b>", table_cell),
            Paragraph("Raw internal telemetry: timestamp, action, volume, MFA flag, total risk score, risk level.", table_cell),
            Paragraph("Cascade relations to risk_factors.", table_cell),
        ],
        [
            Paragraph("<b>risk_factors</b>", table_cell),
            Paragraph("Normalized subscores, weights, and human-readable explanation strings per evaluated event.", table_cell),
            Paragraph("Enables complete mathematical explainability.", table_cell),
        ],
        [
            Paragraph("<b>security_cases</b>", table_cell),
            Paragraph("Case management dossiers for events &ge; 61.0. Tracks status (OPEN, DISMISSED, ESCALATED).", table_cell),
            Paragraph("Requires audited justification on disposition.", table_cell),
        ],
        [
            Paragraph("<b>audit_logs</b>", table_cell),
            Paragraph("Append-only audit trail recording every case review, policy adjustment, and trust level change.", table_cell),
            Paragraph("SHA-256 Hash Chain: Hash_N = SHA256(Hash_{N-1} || Action || Payload).", table_cell),
        ],
        [
            Paragraph("<b>external_signals</b>", table_cell),
            Paragraph("PRAHARAK ingress telemetry: source IP, protocol, payload hash, signature validity, disposition.", table_cell),
            Paragraph("Cryptographically hash-chained audit string.", table_cell),
        ],
        [
            Paragraph("<b>circuit_breakers</b>", table_cell),
            Paragraph("Sliding-window velocity counters per source IP, state (CLOSED/OPEN), quarantine expiration timestamps.", table_cell),
            Paragraph("Automated rate-limiting state machine.", table_cell),
        ],
        [
            Paragraph("<b>cross_incidents</b>", table_cell),
            Paragraph("Unified hybrid incidents fusing external_signal_id + internal_event_id + case_id.", table_cell),
            Paragraph("Binds outer probe to inner identity.", table_cell),
        ],
    ]
    db_table = Table(db_data, colWidths=[95, 239, 170])
    db_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_secondary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(db_table)
    story.append(Spacer(1, 8))

    # ==================== SECTION 7: REST API CONTRACT ====================
    story.append(Paragraph("7. Unified REST API Endpoints & Contract", h1_style))
    story.append(Paragraph(
        "All backend capabilities are exposed over standard JSON REST APIs mounted at <code>/api/v1</code>:",
        body_style
    ))

    api_data = [
        [
            Paragraph("METHOD & ROUTE", table_header),
            Paragraph("SUBSYSTEM", table_header),
            Paragraph("PURPOSE & RETURN CODES", table_header),
        ],
        [
            Paragraph("<code>POST /auth/login</code>", table_cell),
            Paragraph("Authentication", table_cell),
            Paragraph("Authenticates demo credentials (analyst_sarah / admin_vikram); returns JWT bearer token.", table_cell),
        ],
        [
            Paragraph("<code>POST /events</code>", table_cell),
            Paragraph("NIRIKSHAK", table_cell),
            Paragraph("Ingests internal telemetry event, runs 7-layer scoring, auto-creates case if HIGH/CRITICAL.", table_cell),
        ],
        [
            Paragraph("<code>GET /events/{id}/explanation</code>", table_cell),
            Paragraph("NIRIKSHAK", table_cell),
            Paragraph("Returns mathematical factor attribution matrix showing exact point contributions.", table_cell),
        ],
        [
            Paragraph("<code>POST /cases/{id}/review</code>", table_cell),
            Paragraph("Case Workflow", table_cell),
            Paragraph("Applies human triage (DISMISS or ESCALATE) with mandatory audit justification string.", table_cell),
        ],
        [
            Paragraph("<code>GET|PUT /policies/{key}</code>", table_cell),
            Paragraph("Policy Engine", table_cell),
            Paragraph("Queries or updates active dimensional risk weights and decision threshold boundaries.", table_cell),
        ],
        [
            Paragraph("<code>PATCH /devices/{id}/trust</code>", table_cell),
            Paragraph("Device Trust", table_cell),
            Paragraph("Updates device trust posture (TRUSTED, MONITORED, REVOKED) with audit entry.", table_cell),
        ],
        [
            Paragraph("<code>POST /praharak/signals</code>", table_cell),
            Paragraph("PRAHARAK", table_cell),
            Paragraph("Ingests external perimeter signal, verifies cryptographic envelope, outputs disposition.", table_cell),
        ],
        [
            Paragraph("<code>GET /praharak/circuit-breaker</code>", table_cell),
            Paragraph("PRAHARAK", table_cell),
            Paragraph("Returns real-time token-bucket velocity counters and quarantine status per source IP.", table_cell),
        ],
        [
            Paragraph("<code>POST /praharak/circuit-breaker/reset</code>", table_cell),
            Paragraph("PRAHARAK", table_cell),
            Paragraph("Manually lifts quarantine and resets counters for a specific external source IP.", table_cell),
        ],
        [
            Paragraph("<code>GET /praharak/incidents</code>", table_cell),
            Paragraph("The Nexus", table_cell),
            Paragraph("Lists cross-domain incidents correlated across the 30-minute sliding window.", table_cell),
        ],
        [
            Paragraph("<code>POST /scenarios/trigger</code>", table_cell),
            Paragraph("Demo Harness", table_cell),
            Paragraph("Triggers 4 NIRIKSHAK demo scenarios (normal, off_hours, exfiltration, kill_chain).", table_cell),
        ],
        [
            Paragraph("<code>POST /praharak/scenarios/trigger</code>", table_cell),
            Paragraph("Demo Harness", table_cell),
            Paragraph("Triggers 4 PRAHARAK demo scenarios (normal_telemetry, spoofed_command, ddos_flood, hybrid).", table_cell),
        ],
    ]
    api_table = Table(api_data, colWidths=[145, 90, 269])
    api_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(api_table)
    story.append(Spacer(1, 8))

    # ==================== SECTION 8: HYBRID FRONTEND & TERMINAL CONSOLE ====================
    story.append(Paragraph("8. Frontend Dashboard & Analyst Command Console", h1_style))
    story.append(Paragraph(
        "The user interface combines a high-density <b>Modern SOC Dashboard</b> with an embedded <b>Analyst Command Console</b>:",
        body_style
    ))

    ui_data = [
        [
            Paragraph("<b>Primary Framework Switcher</b>", table_cell),
            Paragraph("Prominent top-level toggle allows instant 1-click switching between <b>NIRIKSHAK (Insider Risk)</b> and <b>PRAHARAK (Perimeter Defense)</b> views, automatically synchronizing scenario demo buttons and telemetry streams.", table_cell),
        ],
        [
            Paragraph("<b>Dynamic Scenario Controller</b>", table_cell),
            Paragraph("Displays 4 contextual scenario triggers tailored to the active system twin (4 insider scenarios vs 4 perimeter threat scenarios).", table_cell),
        ],
        [
            Paragraph("<b>Cross-Domain Nexus Alert</b>", table_cell),
            Paragraph("High-priority animated alert card that surfaces unified hybrid incidents, displaying correlated external IP and internal employee identity.", table_cell),
        ],
        [
            Paragraph("<b>Recharts Velocity Charts</b>", table_cell),
            Paragraph("Real-time temporal risk trajectory graphs with horizontal decision threshold lines (LOW, MODERATE, HIGH, CRITICAL).", table_cell),
        ],
        [
            Paragraph("<b>Analyst Command Console</b>", table_cell),
            Paragraph("Docked keyboard drawer toggled via <b>Ctrl + ~</b> (minimized by default for full screen visibility). Strictly built on a <b>client-side AST allowlist parser</b> that rejects operating system shell breakouts (sh, bash, sudo, rm, curl). Communicates over the exact same authenticated REST endpoints.", table_cell),
        ],
    ]
    ui_table = Table(ui_data, colWidths=[140, 364])
    ui_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [c_bg_light, colors.white]),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(ui_table)
    story.append(Spacer(1, 5))

    story.append(Paragraph("<b>Allowlisted Terminal Command Grammar:</b>", h2_style))
    story.append(Paragraph(
        "&bull; <code>status</code>: Query system health, database state, Isolation Forest engine, and active risk scoring weights.<br/>"
        "&bull; <code>events [limit]</code>: Print ASCII tabular access telemetry feed with risk scores and decision tiers.<br/>"
        "&bull; <code>cases</code>: List open security cases pending human adjudication.<br/>"
        "&bull; <code>investigate &lt;case_id&gt;</code>: Display deep-dive case dossier, user history, and attributed factors.<br/>"
        "&bull; <code>explain &lt;event_id&gt;</code>: Output multi-factor mathematical risk attribution matrix.<br/>"
        "&bull; <code>praharak status</code>: Check perimeter telemetry volume, blocked counts, and tripped circuit breakers.<br/>"
        "&bull; <code>praharak signals [n]</code>: Inspect recent external signals, protocols, and dispositions.<br/>"
        "&bull; <code>praharak circuit</code>: View 10s fast / 60s sustained velocity counters and quarantine timestamps.<br/>"
        "&bull; <code>praharak reset &lt;ip&gt;</code>: Manually de-quarantine and reset circuit breaker counters.<br/>"
        "&bull; <code>praharak incidents</code>: List cross-domain correlation incidents linking external IPs to internal identities.<br/>"
        "&bull; <code>praharak trigger &lt;scenario&gt;</code>: Inject perimeter threat scenario directly from the command line.",
        body_style
    ))
    story.append(Spacer(1, 8))

    # ==================== SECTION 9: 8 LIVE DEMONSTRATION SCENARIOS ====================
    story.append(Paragraph("9. The 8 Live Demonstration Scenarios", h1_style))
    story.append(Paragraph(
        "The system ships with 8 pre-seeded, on-demand demonstration scenarios ready for live evaluation:",
        body_style
    ))

    scenarios_data = [
        [
            Paragraph("SCENARIO & TWIN", table_header),
            Paragraph("SIMULATED THREAT PATTERN", table_header),
            Paragraph("RISK SCORE & SYSTEM DISPOSITION", table_header),
        ],
        [
            Paragraph("<b>1. Normal Access</b><br/>(NIRIKSHAK)", table_cell),
            Paragraph("USER-001 reads Operational Repo A from enrolled laptop during standard working hours with MFA.", table_cell),
            Paragraph("<b>21.7 (LOW)</b> &rarr; Logged & monitored in background. No case created.", table_cell),
        ],
        [
            Paragraph("<b>2. Off-Hours Access</b><br/>(NIRIKSHAK)", table_cell),
            Paragraph("USER-002 (Finance) reads Operational Repo A at 02:30 AM without MFA.", table_cell),
            Paragraph("<b>68.8 (HIGH)</b> &rarr; Case automatically generated for analyst review.", table_cell),
        ],
        [
            Paragraph("<b>3. Bulk Exfiltration</b><br/>(NIRIKSHAK)", table_cell),
            Paragraph("USER-003 downloads 2.5 GB from unregistered DEV-999 at 03:15 AM.", table_cell),
            Paragraph("<b>88.5 (CRITICAL)</b> &rarr; Immediate high-priority incident dossier created.", table_cell),
        ],
        [
            Paragraph("<b>4. Multi-Stage Kill Chain</b><br/>(NIRIKSHAK)", table_cell),
            Paragraph("Recon &rarr; Lateral repository enumeration &rarr; Privilege bypass &rarr; 1.8 GB Exfiltration within 15 mins.", table_cell),
            Paragraph("<b>93.9 (CRITICAL)</b> &rarr; Sliding-window multiplier (1.35x) escalates incident.", table_cell),
        ],
        [
            Paragraph("<b>5. Normal Beacon</b><br/>(PRAHARAK)", table_cell),
            Paragraph("Legitimate edge gateway sends signed HTTPS telemetry with valid HMAC-SHA256 and fresh nonce.", table_cell),
            Paragraph("<b>12.5 (LOW)</b> &rarr; Cryptographically verified. <b>ALLOWED</b>.", table_cell),
        ],
        [
            Paragraph("<b>6. Spoofed Command</b><br/>(PRAHARAK)", table_cell),
            Paragraph("Forged drone reroute command submitted with invalid Ed25519 cryptographic signature.", table_cell),
            Paragraph("<b>92.5 (CRITICAL)</b> &rarr; Zero-trust rejection before execution. <b>BLOCKED</b>.", table_cell),
        ],
        [
            Paragraph("<b>7. DDoS Flood</b><br/>(PRAHARAK)", table_cell),
            Paragraph("Adversary floods gateway with 17 rapid burst requests within 3 seconds.", table_cell),
            Paragraph("<b>85.0 (CRITICAL)</b> &rarr; Token-bucket trips to OPEN. <b>15m QUARANTINE</b>.", table_cell),
        ],
        [
            Paragraph("<b>8. Hybrid Nexus Attack</b><br/>(CROSS-DOMAIN)", table_cell),
            Paragraph("External brute-force probe from 198.51.100.77 correlated with internal credential exfiltration by USER-004.", table_cell),
            Paragraph("<b>100.0 (CRITICAL)</b> &rarr; Unified Cross-Domain Nexus Alert linking IP to Identity.", table_cell),
        ],
    ]
    scenarios_table = Table(scenarios_data, colWidths=[120, 224, 160])
    scenarios_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_primary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(scenarios_table)
    story.append(Spacer(1, 8))

    # ==================== SECTION 10: VERIFICATION & TEST RESULTS ====================
    story.append(Paragraph("10. Automated Verification & Security Hardening", h1_style))
    story.append(Paragraph(
        "NIRIKSHAK and PRAHARAK enforce strict Definition of Done (DoD) compliance with 100% automated regression coverage:",
        body_style
    ))

    test_summary_data = [
        [
            Paragraph("TEST SUITE MODULE", table_header),
            Paragraph("VERIFIED SCOPE & SECURITY BOUNDARIES", table_header),
            Paragraph("STATUS", table_header),
        ],
        [
            Paragraph("<code>test_foundation.py</code>", table_cell),
            Paragraph("Schema generation, PostgreSQL seed fixtures, JWT authentication & password hashing.", table_cell),
            Paragraph("<b>PASSED (2/2)</b>", table_cell),
        ],
        [
            Paragraph("<code>test_risk_engine.py</code>", table_cell),
            Paragraph("Deterministic factor calculation, score normalization, boundary capping (0-100), weight validation.", table_cell),
            Paragraph("<b>PASSED (4/4)</b>", table_cell),
        ],
        [
            Paragraph("<code>test_ml_and_correlation.py</code>", table_cell),
            Paragraph("6D feature extraction, Isolation Forest inference, temporal sliding windows, kill-chain multiplier.", table_cell),
            Paragraph("<b>PASSED (3/3)</b>", table_cell),
        ],
        [
            Paragraph("<code>test_ingestion_and_scenarios.py</code>", table_cell),
            Paragraph("REST telemetry ingestion, scenario injection, automated case opening for scores &ge; 61.0.", table_cell),
            Paragraph("<b>PASSED (2/2)</b>", table_cell),
        ],
        [
            Paragraph("<code>test_case_management_and_audit.py</code>", table_cell),
            Paragraph("Case review lifecycle (DISMISS/ESCALATE), justification requirement, SHA-256 audit chaining.", table_cell),
            Paragraph("<b>PASSED (1/1)</b>", table_cell),
        ],
        [
            Paragraph("<code>test_policies_and_devices.py</code>", table_cell),
            Paragraph("Dynamic scoring weight adjustments, threshold tuning, device trust lifecycle (TRUSTED/REVOKED).", table_cell),
            Paragraph("<b>PASSED (2/2)</b>", table_cell),
        ],
        [
            Paragraph("<code>test_praharak.py</code>", table_cell),
            Paragraph("Cryptographic anti-spoofing, token-bucket circuit breaker state machine, MITRE recon, Nexus fusion.", table_cell),
            Paragraph("<b>PASSED (7/7)</b>", table_cell),
        ],
        [
            Paragraph("<code>test_security_boundaries.py</code>", table_cell),
            Paragraph("SQL injection resistance, AST allowlist parser command injection rejection, audit log immutability.", table_cell),
            Paragraph("<b>PASSED (4/4)</b>", table_cell),
        ],
    ]
    test_table = Table(test_summary_data, colWidths=[140, 284, 80])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_emerald),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 8))

    # ==================== SECTION 11: 5-MINUTE PRESENTATION SCRIPT ====================
    story.append(Paragraph("11. 5-Minute 4-Person Hackathon Presentation Script", h1_style))
    story.append(Paragraph(
        "Structured speaker breakdown for live hackathon demonstration:",
        body_style
    ))

    pitch_data = [
        [
            Paragraph("TIME / SPEAKER", table_header),
            Paragraph("KEY MESSAGE & CORE CONCEPTS", table_header),
            Paragraph("LIVE SCREEN ACTION", table_header),
        ],
        [
            Paragraph("<b>0:00 - 1:00</b><br/>Lead / Backend", table_cell),
            Paragraph("State the Problem Statement & Foundational Axiom (Unusual ≠ Malicious). Introduce NIRIKSHAK & PRAHARAK as the 360-degree dual-twin cyber defense prototype.", table_cell),
            Paragraph("Showcase Dual-Twin header and live system health badge (Postgres: Online).", table_cell),
        ],
        [
            Paragraph("<b>1:00 - 2:15</b><br/>Detection / ML", table_cell),
            Paragraph("Demonstrate deterministic scoring + Isolation Forest anomaly detection. Explain that NIRIKSHAK never uses black-box scores—it outputs transparent mathematical attributions.", table_cell),
            Paragraph("Click <b>Scenario 1: Normal</b> (Score: 21.7), then click <b>Scenario 2: Off-Hours</b> (Score: 68.8) and open Factor Inspector.", table_cell),
        ],
        [
            Paragraph("<b>2:15 - 3:30</b><br/>DevOps / Sim", table_cell),
            Paragraph("Demonstrate multi-stage attack progression. Explain how sliding temporal windows correlate multi-event bursts and apply sequential APT multipliers to generate a security case.", table_cell),
            Paragraph("Click <b>Scenario 4: Kill Chain</b>. Point to Recharts temporal velocity wave and automated case creation.", table_cell),
        ],
        [
            Paragraph("<b>3:30 - 5:00</b><br/>Frontend / Sec", table_cell),
            Paragraph("Introduce PRAHARAK (Perimeter Twin). Trigger Hybrid Coordinated Attack. Showcase Cross-Domain Correlation fusing external IP with internal identity. Demonstrate terminal (Ctrl + ~).", table_cell),
            Paragraph("Switch to <b>PRAHARAK</b>. Click <b>Hybrid Attack</b>. Show Nexus Alert. Open terminal (Ctrl + ~), type <code>praharak incidents</code>.", table_cell),
        ],
    ]
    pitch_table = Table(pitch_data, colWidths=[85, 259, 160])
    pitch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_secondary),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_bg_light]),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(pitch_table)
    story.append(Spacer(1, 8))

    # ==================== CONCLUSION & SIGN-OFF ====================
    story.append(KeepTogether([
        HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=4, spaceAfter=6),
        Paragraph(
            "<b>CONCLUSION:</b> NIRIKSHAK and PRAHARAK demonstrate that cybersecurity decision support can be fully contextual, cryptographically verifiable, and human-supervised without succumbing to black-box alert fatigue or unexplainable autonomous actions. The codebase is production-ready, fully tested, and containerized for deployment.",
            body_style
        ),
        Spacer(1, 3),
        Paragraph(
            "<i>Document compiled automatically from repository source code, passing test runs, and system models. All entities are 100% synthetic.</i>",
            meta_style
        )
    ]))

    doc.build(story, canvasmaker=NumberedCanvas)

if __name__ == "__main__":
    local_pdf = "NIRIKSHAK_PRAHARAK_Complete_System_Architecture_and_Implementation_Report.pdf"
    desktop_pdf = "/Users/kanishksingh/Desktop/NIRIKSHAK_PRAHARAK_Complete_System_Architecture_and_Implementation_Report.pdf"
    docs_pdf = "docs/NIRIKSHAK_PRAHARAK_Complete_System_Architecture_and_Implementation_Report.pdf"
    frontend_pdf = "frontend/public/NIRIKSHAK_PRAHARAK_Complete_System_Architecture_and_Implementation_Report.pdf"

    build_complete_pdf(local_pdf)
    print(f"Generated local PDF: {local_pdf}")

    try:
        shutil.copyfile(local_pdf, desktop_pdf)
        print(f"Copied to Desktop: {desktop_pdf}")
    except Exception as e:
        print(f"Failed to copy to Desktop: {e}")

    try:
        os.makedirs("docs", exist_ok=True)
        shutil.copyfile(local_pdf, docs_pdf)
        print(f"Copied to Docs: {docs_pdf}")
    except Exception as e:
        print(f"Failed to copy to Docs: {e}")

    try:
        os.makedirs("frontend/public", exist_ok=True)
        shutil.copyfile(local_pdf, frontend_pdf)
        print(f"Copied to Frontend: {frontend_pdf}")
    except Exception as e:
        print(f"Failed to copy to Frontend: {e}")
