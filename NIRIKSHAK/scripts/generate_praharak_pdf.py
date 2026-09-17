import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
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
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "NIRIKSHAK & PRAHARAK // DEFENSIVE CYBERSECURITY ARCHITECTURE SPECIFICATION")
            self.drawRightString(612 - 54, 750, "CONFIDENTIAL // DEFENSE EVALUATION")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)
        
        self.drawString(54, 32, "PRAHARAK Architectural Specification v1.0 — 100% Synthetic Telemetry")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 32, page_str)
        self.restoreState()

def build_pdf(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0F172A")    # Deep Navy
    c_secondary = colors.HexColor("#1E3A8A")  # Royal Navy
    c_accent = colors.HexColor("#D97706")     # Amber / Saffron
    c_crimson = colors.HexColor("#B91C1C")    # Threat Red
    c_emerald = colors.HexColor("#047857")    # Security Green
    c_text = colors.HexColor("#334155")       # Charcoal
    c_bg_subtle = colors.HexColor("#F8FAFC")  # Off-white
    c_border = colors.HexColor("#E2E8F0")     # Light gray

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceAfter=12,
    )

    badge_style = ParagraphStyle(
        'Badge',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white,
    )

    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=c_secondary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=c_primary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=c_text,
        spaceAfter=6,
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold',
    )

    quote_style = ParagraphStyle(
        'PitchQuote',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=c_text,
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=c_primary,
    )

    table_cell_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    story = []

    # ==================== HEADER BLOCK ====================
    header_data = [
        [
            Paragraph("<b>PROJECT NIRIKSHAK NEXUS</b> &nbsp;|&nbsp; TACTICAL CYBER DEFENSE SPECIFICATION", ParagraphStyle('Meta', fontName='Helvetica-Bold', fontSize=8, textColor=c_accent)),
            Paragraph("CONFIDENTIAL // PROTOTYPE DESIGN", ParagraphStyle('MetaRight', fontName='Helvetica-Bold', fontSize=8, textColor=c_crimson, alignment=2))
        ]
    ]
    t_meta = Table(header_data, colWidths=[350, 154])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 6))

    story.append(Paragraph("PRAHARAK (प्रहारक)", title_style))
    story.append(Paragraph("Outsider-Risk & Perimeter Threat Assessment Architecture<br/><b>The Outward-Facing Twin of NIRIKSHAK</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_secondary, spaceBefore=0, spaceAfter=10))

    # ==================== SECTION 1: CORE PHILOSOPHY ====================
    story.append(Paragraph("1. Core Philosophy: The Architectural Twin Paradigm", h1_style))
    story.append(Paragraph(
        "Modern advanced adversaries do not operate within artificial network silos. Rather than attacking exclusively "
        "from the outside or exclusively from the inside, sophisticated threat campaigns are <b>hybrid</b>: external reconnaissance "
        "identifies a vulnerability, stolen credentials allow perimeter traversal, and internal lateral movement exfiltrates classified data. "
        "To counter this, <b>NIRIKSHAK</b> (the internal observer) and <b>PRAHARAK</b> (the external defender) form a single zero-trust nexus.",
        body_style
    ))

    # Philosophy Comparison Table
    phi_data = [
        [
            Paragraph("System Dimension", table_cell_header),
            Paragraph("NIRIKSHAK (निरीक्षक) — Insider Twin", table_cell_header),
            Paragraph("PRAHARAK (प्रहारक) — Outsider Twin", table_cell_header)
        ],
        [
            Paragraph("<b>Core Question</b>", table_cell_bold),
            Paragraph("<i>'Does this authenticated insider's access make contextual sense?'</i>", table_cell),
            Paragraph("<i>'Does this external request have any right to be here, and is it cryptographically untampered?'</i>", table_cell)
        ],
        [
            Paragraph("<b>Primary Domain</b>", table_cell_bold),
            Paragraph("Internal repositories, IAM credentials, session concurrency, working hour baselines, volume exfiltration.", table_cell),
            Paragraph("Edge perimeters, external API gateways, sensor telemetry, command-and-control spoofing, mass floods.", table_cell)
        ],
        [
            Paragraph("<b>Foundational Axiom</b>", table_cell_bold),
            Paragraph("<b>Unusual Activity ≠ Confirmed Malicious Activity</b> (Decision support, not automated punishment)", table_cell),
            Paragraph("<b>Perimeter Reachability ≠ Execution Rights</b> (Zero trust deserialization, mandatory anti-spoofing)", table_cell)
        ],
        [
            Paragraph("<b>Automated Action</b>", table_cell_bold),
            Paragraph("Human triage queue (Dismiss / Escalate) with explainable factor decomposition.", table_cell),
            Paragraph("Proportional containment: Allow, Challenge, Throttle, or Circuit Breaker Trip.", table_cell)
        ],
    ]
    t_phi = Table(phi_data, colWidths=[110, 197, 197])
    t_phi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_secondary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_subtle]),
    ]))
    story.append(t_phi)
    story.append(Spacer(1, 10))

    # ==================== SECTION 2: 7-STAGE PIPELINE ====================
    story.append(Paragraph("2. The Seven-Stage Ingress & Inspection Pipeline", h1_style))
    story.append(Paragraph(
        "Every incoming packet, tactical command, or external API connection is routed through a deterministic, strictly ordered 7-stage pipeline:",
        body_style
    ))

    pipe_data = [
        [Paragraph("Stage", table_cell_header), Paragraph("Pipeline Phase", table_cell_header), Paragraph("Inspection Logic & Defense Guarantee", table_cell_header)],
        [Paragraph("<b>1</b>", table_cell_bold), Paragraph("<b>Origin & Identity Check</b>", table_cell_bold), Paragraph("Validates source IP, BGP ASN reputation, enrolled edge gateways, and flags commercial VPN/Tor exit clusters.", table_cell)],
        [Paragraph("<b>2</b>", table_cell_bold), Paragraph("<b>Cryptographic Integrity Check</b>", table_cell_bold), Paragraph("<b>Anti-Spoofing:</b> Verifies Ed25519/HMAC-SHA256 signatures, timestamp freshness (Δt ≤ 120s), and nonces before deserialization.", table_cell)],
        [Paragraph("<b>3</b>", table_cell_bold), Paragraph("<b>Pattern & Threat Intel Match</b>", table_cell_bold), Paragraph("Cross-references dynamic IOC threat feeds and maps reconnaissance sweeps directly to MITRE ATT&CK tactics.", table_cell)],
        [Paragraph("<b>4</b>", table_cell_bold), Paragraph("<b>Velocity & Circuit Breaker</b>", table_cell_bold), Paragraph("Sliding-window token bucket (10s & 60s). Automatically trips circuit breaker during floods, isolating the source.", table_cell)],
        [Paragraph("<b>5</b>", table_cell_bold), Paragraph("<b>Explainable Threat Scoring</b>", table_cell_bold), Paragraph("Calculates normalized threat score (0–100) and produces quantified factor attributions with plain-language rationale.", table_cell)],
        [Paragraph("<b>6</b>", table_cell_bold), Paragraph("<b>Proportional Response</b>", table_cell_bold), Paragraph("Enforces graduated response: <i>Allow</i> (0-30), <i>Challenge</i> (31-60), <i>Throttle/Quarantine</i> (61-80), <i>Block & Alert</i> (81-100).", table_cell)],
        [Paragraph("<b>7</b>", table_cell_bold), Paragraph("<b>Cross-Domain Correlation</b>", table_cell_bold), Paragraph("<b>The Nexus:</b> Correlates external event with internal NIRIKSHAK telemetry to catch hybrid kill-chains in real time.", table_cell)],
    ]
    t_pipe = Table(pipe_data, colWidths=[35, 145, 324])
    t_pipe.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, c_bg_subtle]),
    ]))
    story.append(t_pipe)
    story.append(Spacer(1, 10))

    # ==================== SECTION 3: 10 FULL FEATURES ====================
    story.append(Paragraph("3. Full Feature Breakdown & Engineering Specifications", h1_style))

    # Features list with bold callouts
    feats = [
        ("1. Perimeter & Network Intrusion Detection",
         "Continuously monitors edge ingress points, ingress controllers, and firewall telemetry. Flags known-malicious IP ranges, bulletproof hosters, and suspicious ASN hops. Detects port-knocking and horizontal subnet sweeping during the attacker's preliminary 'testing the locks' phase."),
        
        ("2. Cryptographic Command & Signal Spoofing Detection ⭐ (STANDOUT FEATURE)",
         "Traditional firewalls only check IP source addresses—which can be spoofed or route-hijacked. PRAHARAK mandates <b>zero-trust deserialization</b>: every incoming tactical command (fire order, drone reroute, actuator signal) is signed with an asymmetric key or HMAC. If signature verification fails or the nonce is replayed, the packet is rejected at the network boundary <b>before deserialization or execution</b>."),
        
        ("3. Reconnaissance Pattern Recognition (MITRE ATT&CK Mapped)",
         "Identifies scanning, parameter probing, and credential spraying prior to a full breach attempt. Detected behavior is mapped directly to standard MITRE ATT&CK techniques (T1595 Active Scanning, T1110 Credential Access, T1190 Exploit Public Application, T1071 C2 Protocol), giving analysts actionable threat taxonomy."),
        
        ("4. Mass-Attack / Flood Detection with Graduated Circuit Breaker ⭐ (STANDOUT FEATURE)",
         "High-velocity DDoS or command-injection bursts overwhelm human analysts with alert floods. PRAHARAK employs a multi-window sliding token bucket with an automated state machine (<code>CLOSED</code> → <code>HALF-OPEN</code> → <code>OPEN</code>). When tripped, it restricts traffic at the edge socket level for a 15-minute quarantine, aggregating the flood into a single incident card rather than thousands of spam alerts."),
        
        ("5. Explainable External Threat Scoring",
         "Every flagged external interaction includes a mathematical factor decomposition. Analysts never see a black-box 'BLOCKED' label; they receive exact point contributions (e.g. <i>30% Signature Mismatch, 20% Unknown ASN, 19.5% Velocity Spike</i>) with human-readable rationale to expedite manual verification."),
        
        ("6. Dynamic Threat Intelligence Feed Correlation",
         "Ingests and normalizes real-time threat intelligence feeds into an in-memory radix tree for sub-millisecond CIDR matching against active threat actor infrastructure, botnets, and command-and-control dropsites."),
        
        ("7. Cross-Domain Correlation with NIRIKSHAK ⭐ (CORE DIFFERENTIATOR)",
         "<b>The Grand Slam Feature:</b> Most real-world attacks are hybrid—external reconnaissance followed by lateral movement with stolen internal credentials. PRAHARAK and NIRIKSHAK share a unified correlation core. If an external scan targets an endpoint and, within minutes, an internal user accesses that sensitive repository from an unfamiliar location, the system fuses both into a single <b>CRITICAL Hybrid Kill-Chain Incident</b>."),
        
        ("8. Tamper-Proof Cryptographic Audit Trail",
         "Every external event, signature check, circuit trip, and triage action is committed to an append-only SHA-256 hash-chained ledger (H_k = SHA256(H_{k-1} || Data_k)). This produces a mathematically immutable, court-admissible forensic record of any attempted breach."),
        
        ("9. Quantum-Resistant Hybrid Cryptography (PQC Readiness)",
         "Incorporates hybrid signature verification combining classical Ed25519 with NIST FIPS 204 ML-DSA (Dilithium-3) and NIST FIPS 203 ML-KEM (Kyber-768). Guarantees tactical control signals remain immune to 'harvest now, decrypt later' quantum computing attacks."),
        
        ("10. Proportional Response Matrix",
         "Applies graduated operational responses: <b>LOW (0–30)</b> logs and updates baselines; <b>MODERATE (31–60)</b> challenges via proof-of-work or re-handshake; <b>HIGH (61–80)</b> enforces an 80% bandwidth throttle and queues analyst review; <b>CRITICAL (81–100)</b> trips the circuit breaker and triggers an emergency command alert.")
    ]

    for title, desc in feats:
        story.append(Paragraph(title, h2_style))
        story.append(Paragraph(desc, body_style))
        story.append(Spacer(1, 2))

    # ==================== SECTION 4: MATHEMATICAL FORMULATION ====================
    story.append(Spacer(1, 4))
    story.append(Paragraph("4. Mathematical Formulation & Factor Attribution", h1_style))
    story.append(Paragraph(
        "PRAHARAK adheres strictly to deterministic, explainable risk scoring. The external threat score is defined as:",
        body_style
    ))

    # Math formula block
    math_data = [
        [
            Paragraph(
                "<b>Risk<sub>Outsider</sub>(E<sub>ext</sub>) = ∑<sub>j ∈ F</sub> w<sub>j</sub> · S<sub>j</sub>(E<sub>ext</sub>)</b><br/>"
                "&nbsp;&nbsp;&nbsp;&nbsp;Where: F = {Origin (0.20), Integrity (0.30), Recon (0.20), Velocity (0.15), ThreatIntel (0.15)}<br/>"
                "&nbsp;&nbsp;&nbsp;&nbsp;Normalized Bounds: S<sub>j</sub> ∈ [0.0, 100.0], &nbsp; ∑ w<sub>j</sub> = 1.0, &nbsp; Risk<sub>Outsider</sub> ∈ [0.0, 100.0]",
                ParagraphStyle('MathBox', fontName='Courier-Bold', fontSize=8.5, leading=12, textColor=c_primary)
            )
        ]
    ]
    t_math = Table(math_data, colWidths=[504])
    t_math.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_bg_subtle),
        ('BOX', (0,0), (-1,-1), 1, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_math)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Cross-Domain Unified Correlation Formulation:</b><br/>"
        "When an external event E<sub>ext</sub> and an internal access event E<sub>int</sub> share temporal proximity (Δt ≤ 30 min) "
        "and departmental linkage, the shared nexus computes the unified incident score:",
        body_style
    ))

    math_data2 = [
        [
            Paragraph(
                "<b>Risk<sub>Unified</sub> = min(100.0, &nbsp; max(Risk<sub>ext</sub>, Risk<sub>int</sub>) · Φ<sub>cross-domain</sub>)</b><br/>"
                "&nbsp;&nbsp;&nbsp;&nbsp;Where Φ<sub>cross-domain</sub> = 1.35 (Amplifier triggered by simultaneous external probe & internal deviation).<br/>"
                "&nbsp;&nbsp;&nbsp;&nbsp;Instantly elevates ambiguous low/moderate events into a unified <b>CRITICAL (≥ 85.0)</b> incident.",
                ParagraphStyle('MathBox2', fontName='Courier-Bold', fontSize=8.5, leading=12, textColor=c_crimson)
            )
        ]
    ]
    t_math2 = Table(math_data2, colWidths=[504])
    t_math2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FEF2F2")),
        ('BOX', (0,0), (-1,-1), 1, c_crimson),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_math2)
    story.append(Spacer(1, 10))

    # ==================== SECTION 5: COMMANDER'S PITCH ====================
    story.append(Paragraph("5. The Tactical Officer Pitch: Why This Wins in Real Defense", h1_style))
    
    pitch_data = [
        [
            Paragraph(
                "<i>\"Most cyber defense failures don't happen because an organization lacked a perimeter firewall, "
                "and they don't happen because they lacked internal access control. They happen because real-world attacks are hybrid.<br/><br/>"
                "An adversary scans from the outside, finds an entry point, steals or compromises an insider's credential, "
                "and immediately walks past the perimeter. From that exact second forward, traditional perimeter tools believe 'the attacker left,' "
                "and internal tools believe 'a legitimate insider arrived.'<br/><br/>"
                "<b>PRAHARAK and NIRIKSHAK eliminate this operational blind spot.</b> By deploying twin engines over a shared correlation core, "
                "the instant external reconnaissance occurs at the edge, internal telemetry is primed. If that identity is used moments later "
                "in an anomalous manner, the system doesn't generate two disconnected, low-priority alerts sitting in two separate dashboards—it "
                "synthesizes a single, unified CRITICAL incident, automatically trips the perimeter circuit breaker, and presents an explainable, "
                "court-admissible audit trail directly to the commander.\"</i>",
                quote_style
            )
        ]
    ]
    t_pitch = Table(pitch_data, colWidths=[504])
    t_pitch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EFF6FF")),
        ('BOX', (0,0), (-1,-1), 1.2, c_secondary),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_pitch)
    story.append(Spacer(1, 12))

    # ==================== SECTION 6: IMPLEMENTATION REPO STATUS ====================
    story.append(Paragraph("6. Architecture & System Artifacts", h1_style))
    story.append(Paragraph(
        "• <b>Complete Architecture Specification:</b> <code>docs/PRAHARAK_ARCHITECTURE.md</code><br/>"
        "• <b>Core Framework Repository:</b> NIRIKSHAK (Contextual Insider-Risk Decision Support Prototype)<br/>"
        "• <b>Data & Telemetry Model:</b> 100% Synthetic identities (<code>USER-001</code> to <code>USER-010</code>) and synthetic resources.<br/>"
        "• <b>Security Guarantees:</b> Zero-trust deserialization, SHA-256 hash-chained audit logging, deterministic explainability.",
        body_style
    ))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {filename}")

    # Copy to Desktop if available
    desktop_path = os.path.expanduser("~/Desktop")
    if os.path.exists(desktop_path):
        import shutil
        dest = os.path.join(desktop_path, os.path.basename(filename))
        try:
            shutil.copy2(filename, dest)
            print(f"Copied PDF to Desktop: {dest}")
        except Exception as e:
            print(f"Could not copy to Desktop: {e}")

if __name__ == "__main__":
    out_path = sys.argv[1] if len(sys.argv) > 1 else "PRAHARAK_Architecture_and_Feature_Specification.pdf"
    build_pdf(out_path)
