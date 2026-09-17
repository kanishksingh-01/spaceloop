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
    """Two-pass canvas for crisp running headers, footers, and dynamic page counts."""
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
            self.drawString(54, 750, "SPACELOOP // COMPLETE SYSTEM FEATURES & ARCHITECTURAL SPECIFICATION")
            self.drawRightString(612 - 54, 750, "HACK2IGNITE 2026 // ENGINEERING REPORT")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 42, 612 - 54, 42)
        
        self.drawString(54, 30, "SpaceLoop — AI-Powered Micro-Space Marketplace & Adaptive Micro-Leasing Engine")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 30, page_str)
        self.restoreState()


def create_callout_box(title, text, bg_color="#F8FAFC", border_color="#CBD5E1", title_color="#0F172A", body_style=None):
    content = []
    if title:
        content.append(Paragraph(f"<b>{title}</b>", ParagraphStyle(
            'CalloutTitle_' + title[:12].replace(' ', '_').replace(':', ''),
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor(title_color),
            spaceAfter=3
        )))
    content.append(Paragraph(text, body_style))
    
    t = Table([[content]], colWidths=[504])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
        ('BOX', (0,0), (-1,-1), 0.75, colors.HexColor(border_color)),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 9),
    ]))
    return t


def generate_spaceloop_pdf(output_filename="SpaceLoop_Complete_Features_Specification.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Palette
    c_primary = colors.HexColor("#0F172A")
    c_blue = colors.HexColor("#2563EB")
    c_text = colors.HexColor("#334155")
    c_muted = colors.HexColor("#64748B")
    c_border = colors.HexColor("#E2E8F0")

    title_style = ParagraphStyle(
        'SLTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=3,
    )

    subtitle_style = ParagraphStyle(
        'SLSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=c_blue,
        spaceAfter=8,
    )

    meta_style = ParagraphStyle(
        'SLMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=c_muted,
    )

    h1_style = ParagraphStyle(
        'SLH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15.5,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        'SLH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13.5,
        textColor=c_blue,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        'SLBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.25,
        leading=11.75,
        textColor=c_text,
        spaceAfter=3.5,
    )

    table_header_style = ParagraphStyle(
        'SLTH',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.75,
        leading=10.5,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        'SLTD',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.25,
        leading=10,
        textColor=c_text,
    )

    table_cell_bold = ParagraphStyle(
        'SLTDBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.25,
        leading=10,
        textColor=c_primary,
    )

    story = []

    # =========================================================================
    # PAGE 1: TITLE, EXECUTIVE OVERVIEW, AND FOUNDATIONAL ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("SpaceLoop: Complete Features & Architectural Specification", title_style))
    story.append(Paragraph("A Mid-Detailed Engineering Dossier on AI Capabilities, Zero-Hardware Protocols & Micro-Leasing", subtitle_style))

    meta_table = Table([
        [
            Paragraph("<b>Project:</b> SpaceLoop (Built for Hack2Ignite 2026)", meta_style),
            Paragraph("<b>Version:</b> 2.4 (Production Architecture)", meta_style),
            Paragraph("<b>Stack:</b> Python / Flask / SQLite / Dual LLMs", meta_style),
        ],
        [
            Paragraph("<b>Lead Dev:</b> Kanishk Singh", meta_style),
            Paragraph("<b>Compliance:</b> DPDP Act 2023 & India Stack", meta_style),
            Paragraph("<b>Deployment:</b> Live Cloud + Render Blueprint", meta_style),
        ]
    ], colWidths=[175, 160, 169])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1. Executive Overview & The Problem Solved", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=c_blue, spaceBefore=1, spaceAfter=5))
    story.append(Paragraph(
        "Modern metropolitan areas suffer from a pronounced real estate inefficiency paradox: hundreds of millions of square feet sit vacant or "
        "severely underutilized during daytime and off-peak hours (empty residential garages, daytime-vacant basements, retail storefronts idle after 4 PM, "
        "private driveways during working hours, and off-peak cafés). Simultaneously, students, digital creators, remote freelancers, and micro-entrepreneurs "
        "face prohibitive barriers—rigid 12-month commercial leases, $400+/day production studios, and multi-month security deposits. "
        "SpaceLoop solves this disparity by converting idle urban square footage into liquid, on-demand, temporary micro-rentals "
        "(by the hour or day) backed by automated legal safeguards, multimodal spatial inspection, and zero-hardware access protocols.",
        body_style
    ))

    callout_arch = (
        "<b>Multi-Tier Intelligence Hierarchy:</b> SpaceLoop deploys a three-tier resilient AI framework. High-complexity spatial "
        "inspections and conversational search queries route first to <b>Groq (Llama-3.3-70B-Versatile)</b> for sub-second responses (<450ms). "
        "If Groq experiences rate limits or network issues, requests automatically fall over to <b>Google Gemini 1.5 Flash</b>. In offline, "
        "air-gapped, or degraded connectivity scenarios, a deterministic rule-based heuristic engine guarantees 100% platform uptime."
    )
    story.append(create_callout_box("Architectural Core: High-Availability Dual-AI Engine", callout_arch, "#EFF6FF", "#93C5FD", "#1E40AF", body_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Key Market Dynamics & Operational Comparison", h2_style))
    market_table_data = [
        [Paragraph("Platform / Model", table_header_style), Paragraph("Target Use Case", table_header_style), Paragraph("Hardware & Capital Barrier", table_header_style), Paragraph("Legal Tenancy Risk", table_header_style)],
        [
            Paragraph("<b>Airbnb / Vrbo</b>", table_cell_bold),
            Paragraph("Multi-day overnight hospitality", table_cell_style),
            Paragraph("High host furnishing & smart lock CapEx", table_cell_style),
            Paragraph("High risk of overstay & squatting", table_cell_style),
        ],
        [
            Paragraph("<b>Commercial Leases</b>", table_cell_bold),
            Paragraph("Multi-year office / retail space", table_cell_style),
            Paragraph("Predatory multi-month security deposits", table_cell_style),
            Paragraph("Rigid statutory tenancy leasehold", table_cell_style),
        ],
        [
            Paragraph("<b>SpaceLoop (Ours)</b>", table_cell_bold),
            Paragraph("<b>On-demand micro-utility (1–8 hrs)</b>", table_cell_style),
            Paragraph("<b>₹0 Hardware (GPS + Laminated QR)</b>", table_cell_style),
            Paragraph("<b>Revocable License (Zero Tenancy)</b>", table_cell_style),
        ],
    ]
    t_market = Table(market_table_data, colWidths=[110, 130, 134, 130])
    t_market.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_market)

    # =========================================================================
    # PAGE 2: COMPLETE MASTER FEATURE BREAKDOWN MATRIX
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("2. Master Subsystems & Feature Breakdown Matrix", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=c_blue, spaceBefore=1, spaceAfter=5))
    story.append(Paragraph(
        "SpaceLoop comprises 12 interconnected subsystems spanning computer vision, legal contract automation, fintech escrow, "
        "and physical access verification. The matrix below outlines each capability, its technical implementation, and operational impact:",
        body_style
    ))
    story.append(Spacer(1, 4))

    matrix_data = [
        [
            Paragraph("Subsystem / Feature", table_header_style),
            Paragraph("Domain", table_header_style),
            Paragraph("Core Technology", table_header_style),
            Paragraph("Operational Function & Impact", table_header_style),
        ],
        [
            Paragraph("<b>1. Multimodal Space Inspector</b>", table_cell_bold),
            Paragraph("Spatial AI", table_cell_style),
            Paragraph("Groq Llama 3.3 70B / Gemini 1.5", table_cell_style),
            Paragraph("Extracts sqft, lighting, acoustic dB (<36dB), circuit load, and auto-generates high-converting listing copy.", table_cell_style),
        ],
        [
            Paragraph("<b>2. Conversational Matchmaker</b>", table_cell_bold),
            Paragraph("NLP Search", table_cell_style),
            Paragraph("Semantic Intent Parser + Scorer", table_cell_style),
            Paragraph("Parses conversational renter queries; outputs a 0–100% Compatibility Score with pros/cons breakdown.", table_cell_style),
        ],
        [
            Paragraph("<b>3. AI Micro-Lease Synthesizer</b>", table_cell_bold),
            Paragraph("Legal Tech", table_cell_style),
            Paragraph("LLM Contract Engine (Sec 52)", table_cell_style),
            Paragraph("Synthesizes enforceable Revocable License Agreements; prevents tenancy rights and caps host liability.", table_cell_style),
        ],
        [
            Paragraph("<b>4. Dynamic Pricing Calculator</b>", table_cell_bold),
            Paragraph("Economics", table_cell_style),
            Paragraph("SqFt Polynomial Multiplier Model", table_cell_style),
            Paragraph("Computes hourly/daily pricing baselines; projects monthly passive income and commercial lease savings.", table_cell_style),
        ],
        [
            Paragraph("<b>5. Zero-Hardware Access Suite</b>", table_cell_bold),
            Paragraph("Physical Access", table_cell_style),
            Paragraph("Haversine GPS + 4-Digit Handshake", table_cell_style),
            Paragraph("Enables physical access verification via laminated door QRs and rotating PINs without smart lock costs.", table_cell_style),
        ],
        [
            Paragraph("<b>6. CV Room Condition Delta</b>", table_cell_bold),
            Paragraph("Computer Vision", table_cell_style),
            Paragraph("Visual Diff + Appliance Detection", table_cell_style),
            Paragraph("Compares entry vs exit photos; verifies fan/light shutdown and auto-approves instant UPI escrow release.", table_cell_style),
        ],
        [
            Paragraph("<b>7. Student Academic Verification</b>", table_cell_bold),
            Paragraph("India Stack", table_cell_style),
            Paragraph("Domain Regex (.ac.in) + ID Masking", table_cell_style),
            Paragraph("Validates enrolled student credentials for subsidized study rates while masking sensitive identity data.", table_cell_style),
        ],
        [
            Paragraph("<b>8. DigiLocker Aadhaar OTP</b>", table_cell_bold),
            Paragraph("KYC & DPDP", table_cell_style),
            Paragraph("DPDP Salted SHA-256 Hash Token", table_cell_style),
            Paragraph("Zero raw Aadhaar storage; masks display to XXXX-XXXX-1234 and secures user privacy under DPDP Act 2023.", table_cell_style),
        ],
        [
            Paragraph("<b>9. Host Electricity Bill (Discom)</b>", table_cell_bold),
            Paragraph("Property Proof", table_cell_style),
            Paragraph("BBPS / Discom CA Number Lookup", table_cell_style),
            Paragraph("Cross-verifies utility consumer accounts (BESCOM, TPDDL) to confirm legal possession of space.", table_cell_style),
        ],
        [
            Paragraph("<b>10. NPCI UPI ₹1 Penny Drop</b>", table_cell_bold),
            Paragraph("FinTech KYC", table_cell_style),
            Paragraph("NPCI UPI VPA Resolution API", table_cell_style),
            Paragraph("Validates host bank account title via penny drop before payout activation to prevent fraud.", table_cell_style),
        ],
        [
            Paragraph("<b>11. Objective Trust Index (OTI)</b>", table_cell_bold),
            Paragraph("Reputation", table_cell_style),
            Paragraph("Multi-Variate Telemetry Scoring", table_cell_style),
            Paragraph("Replaces biased 5-star reviews; weights punctuality (35%), cleanliness (35%), KYC (20%), and disputes (10%).", table_cell_style),
        ],
        [
            Paragraph("<b>12. LoopBot AI Concierge</b>", table_cell_bold),
            Paragraph("AI Assistant", table_cell_style),
            Paragraph("Context-Aware Multi-Turn LLM Bot", table_cell_style),
            Paragraph("Assists seekers with space recommendations, helps hosts optimize rates, and pre-answers inquiries.", table_cell_style),
        ],
    ]

    t_matrix = Table(matrix_data, colWidths=[115, 75, 130, 184])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_matrix)
    story.append(Spacer(1, 6))

    flow_box = (
        "<b>End-to-End User Journey:</b> Host uploads space photo &rarr; AI Inspector calculates specs & sets baseline dynamic rate &rarr; "
        "Listing goes live &rarr; Renter searches in natural language &rarr; AI Matchmaker ranks spaces with compatibility score &rarr; "
        "Renter books space &rarr; AI synthesizes customized Micro-Lease &rarr; Renter arrives and checks in via GPS & Door QR &rarr; "
        "Renter completes session and submits checkout scan &rarr; AI evaluates condition delta &rarr; Instant ₹100 UPI escrow deposit refund."
    )
    story.append(create_callout_box("End-to-End Platform Lifecycle", flow_box, "#F1F5F9", "#CBD5E1", "#0F172A", body_style))

    # =========================================================================
    # PAGE 3: TECHNICAL DEEP-DIVE: FEATURES 1 TO 4
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Technical Deep-Dive: Spatial AI, Discovery & Micro-Leasing", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=c_blue, spaceBefore=1, spaceAfter=6))

    # Feature 1
    story.append(Paragraph("Feature 1: Multimodal AI Space Inspector", h2_style))
    story.append(Paragraph(
        "<b>Challenge:</b> Manual listing creation is tedious and inaccurate. Property hosts rarely know exact square footage, "
        "electrical circuit loads, or how to craft high-converting marketing descriptions.<br/>"
        "<b>Architecture:</b> When a host uploads property imagery and unstructured notes (e.g. <i>'quiet 2-car garage with white walls and lots of plugs'</i>), "
        "the AI Space Inspector executes a structured multi-phase analysis: "
        "<br/>• <b>Spatial Metric Estimation:</b> Estimates usable floor area (30–25,000 sq ft) and maximum occupancy capacity."
        "<br/>• <b>Environmental Profiling:</b> Categorizes natural vs artificial illumination (e.g. <i>'Bright Natural Sunlit with Sheer Diffusers'</i>) and background acoustics (e.g. <i>'Quiet (<38 dB)'</i>)."
        "<br/>• <b>Power Infrastructure:</b> Detects electrical outlets and circuits (e.g. <i>'4x Grounded 20A Circuits + Level 2 EV Charger'</i>)."
        "<br/>• <b>Security Guardrails:</b> Host notes are isolated within strict XML tags (<code>&lt;user_untrusted_notes&gt;</code>) to prevent prompt injection and system instruction leaks.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Feature 2
    story.append(Paragraph("Feature 2: Natural Language Semantic Matchmaker", h2_style))
    story.append(Paragraph(
        "<b>Challenge:</b> Dropdown filters fail when seekers have nuanced, activity-specific criteria.<br/>"
        "<b>Architecture:</b> Seekers type conversational search queries such as: "
        "<i>'Need an acoustically quiet studio for a 3-person podcast recording this Saturday under $40/hr with good Wi-Fi.'</i><br/>"
        "• The semantic parser extracts intent vectors: domain (Podcast), capacity (3 pax), acoustic needs (quiet), budget ($40/hr), and essential amenities."
        "<br/>• Evaluates candidate spaces in real time and computes a <b>0–100% Compatibility Score</b>."
        "<br/>• Returns diagnostic badges (<i>'Top Pick'</i>, <i>'Great Match'</i>, <i>'Alternative'</i>), specific pros/cons, and budget compliance notes."
        "<br/>• Supported by a rule-based fallback keyword engine guaranteeing zero query failures even if external LLM APIs are offline.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Feature 3
    story.append(Paragraph("Feature 3: Automated Plain-English AI Micro-Lease Synthesizer", h2_style))
    story.append(Paragraph(
        "<b>Legal Innovation & Tenancy Prevention:</b> The biggest concern for property owners is tenant squatting and legal lease lock-in. "
        "In India, long-term tenancy falls under the Transfer of Property Act 1882 (Section 105), which grants heavy tenant protections. "
        "SpaceLoop completely eliminates this friction by algorithmically generating an enforceable, plain-English <b>Temporary Space Use License Agreement</b> "
        "under <b>Section 52 of the Indian Easements Act, 1882</b>.<br/>"
        "• <b>Revocable License Clause:</b> Explicitly stipulates that no tenancy or leasehold interest is created; access is strictly a revocable personal license."
        "<br/>• <b>Activity-Bound Scope:</b> Confines permission strictly to the declared activity (e.g. study session, video shoot), prohibiting subletting or unauthorized retail."
        "<br/>• <b>Liquidated Overstay Damages:</b> Automatically charges an overtime penalty of <b>1.5x the hourly rate</b> in 30-minute increments for late vacating."
        "<br/>• <b>Mutual Indemnification:</b> Shifts premises liability for personal belongings and minor injury onto the licensee, protecting the property owner.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Feature 4
    story.append(Paragraph("Feature 4: Dynamic Micro-Pricing & Passive Revenue Calculator", h2_style))
    story.append(Paragraph(
        "<b>Economics Engine:</b> SpaceLoop deploys an automated non-linear pricing model designed to maximize host occupancy while providing 60–75% cost savings to renters: "
        "<br/>• <b>Category Baseline Rates:</b> Storage (₹35/hr), Studio (₹65/hr), Parking (₹25/hr), Pop-up/Retail (₹95/hr), Event (₹85/hr), Workspace (₹45/hr)."
        "<br/>• <b>Non-Linear SqFt Scaling:</b> Evaluates <code>sqft_adj = max(0.8, min(2.5, sqft / 250.0))</code> with dampening formula <code>Rate = Base * (0.6 + 0.4 * sqft_adj)</code>."
        "<br/>• <b>Yield Projections:</b> Calculates projected monthly net income assuming a realistic 12-day monthly occupancy, deducting the 15% platform service fee.",
        body_style
    ))

    # =========================================================================
    # PAGE 4: ZERO HARDWARE, COMPUTER VISION & OBJECTIVE TRUST
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("Features 5 – 8: Zero-Hardware Physical Access & Objective Trust", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=c_blue, spaceBefore=1, spaceAfter=6))

    story.append(Paragraph("Feature 5: Zero-Hardware Smart Access Protocol", h2_style))
    story.append(Paragraph(
        "<b>Why Zero-Hardware?</b> Smart IoT locks cost $150–$300 per door, demand reliable 24/7 Wi-Fi, and fail during power outages. "
        "In developing urban environments, smart locks represent an impossible financial barrier for spare spaces. "
        "SpaceLoop introduces a zero-CapEx, four-layered access architecture:",
        body_style
    ))

    zh_table_data = [
        [Paragraph("Access Mechanism", table_header_style), Paragraph("Hardware Cost", table_header_style), Paragraph("Security & Verification Protocol", table_header_style)],
        [
            Paragraph("<b>1. GPS Haversine Geofence</b>", table_cell_bold),
            Paragraph("₹0 (Smartphone GPS)", table_cell_style),
            Paragraph("Calculates real-time distance using Haversine formula; restricts check-in strictly to within 30–50m radius of property coordinates.", table_cell_style),
        ],
        [
            Paragraph("<b>2. Printable Cryptographic Door QR</b>", table_cell_bold),
            Paragraph("₹10 (Laminated Sheet)", table_cell_style),
            Paragraph("Affixed to entrance door. Encodes a 64-character cryptographic SHA-256 room token verified upon camera scan.", table_cell_style),
        ],
        [
            Paragraph("<b>3. Caretaker Handshake PIN</b>", table_cell_bold),
            Paragraph("₹0 (Verbal / WhatsApp)", table_cell_style),
            Paragraph("Rotating 4-digit PIN generated per booking. Guest presents code to on-site guard or caretaker for physical gate entry.", table_cell_style),
        ],
        [
            Paragraph("<b>4. Mechanical Keybox</b>", table_cell_bold),
            Paragraph("₹800 (One-time mechanical)", table_cell_style),
            Paragraph("Weatherproof 4-wheel mechanical key lockbox. The master key is stored inside; combination code rotates per reservation.", table_cell_style),
        ],
    ]
    t_zh = Table(zh_table_data, colWidths=[130, 95, 279])
    t_zh.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_zh)
    story.append(Spacer(1, 5))

    # Feature 6
    story.append(Paragraph("Feature 6: Computer Vision Room Condition Delta Evaluation", h2_style))
    story.append(Paragraph(
        "<b>Automated Inspection & Escrow Release:</b> Hosts cannot physically inspect rooms after every 2-hour rental. "
        "SpaceLoop solves this with an automated multimodal Computer Vision pipeline at check-out: "
        "<br/>• <b>Visual Diff Analysis:</b> The renter captures a photo scan of the room upon departure, which is compared against the check-in baseline."
        "<br/>• <b>Cleanliness & Waste Detection:</b> Flags abandoned garbage, drink cans, or misplaced furniture."
        "<br/>• <b>Appliance & Energy Conservation Check:</b> Confirms whether ceiling fans, lights, and air conditioners have been powered off."
        "<br/>• <b>Instant Escrow Refund:</b> Upon passing the AI inspection (Condition Match Score &ge; 90%), the system programmatically triggers the instant release of the <b>₹100 UPI security deposit</b> back to the renter's account.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Feature 7
    story.append(Paragraph("Feature 7: India-First Trust & Document Verification Suite", h2_style))
    story.append(Paragraph(
        "To establish unquestioned institutional trust, SpaceLoop incorporates four integrated verification gateways: "
        "<br/>• <b>7A. Student Academic Verification:</b> Validates academic credentials via institutional email domain handshakes (e.g. <code>.ac.in</code>, <code>.edu.in</code>) or student ID uploads, unlocking subsidized rates while masking IDs (e.g. <code>STU-***-4821</code>)."
        "<br/>• <b>7B. DigiLocker Aadhaar OTP (DPDP Act 2023 Compliant):</b> Complies with the Digital Personal Data Protection Act 2023 by never storing raw Aadhaar digits. Generates a salted SHA-256 hash and masks the UI display to <code>XXXX-XXXX-4821</code>."
        "<br/>• <b>7C. Host Electricity Bill (Discom) Verification:</b> Eliminates fake listings by verifying the host's Consumer Account (CA) number against state power distribution utilities (BESCOM, TPDDL, MSEDCL), confirming legal possession of the physical premises."
        "<br/>• <b>7D. NPCI UPI ₹1 Penny Drop Verification:</b> Validates the host's bank account title against their registered identity, guaranteeing zero failed payouts.",
        body_style
    ))
    story.append(Spacer(1, 4))

    # Feature 8
    story.append(Paragraph("Feature 8: Objective Trust Index (OTI) Telemetry Engine", h2_style))
    formula_text = (
        "<b>OTI Formulation:</b> &nbsp;&nbsp;<b>OTI = (0.35 × Punctuality) + (0.35 × Cleanliness) + (0.20 × Identity Trust) + (0.10 × Dispute History)</b><br/>"
        "• <b>Punctuality (35%):</b> Logged from GPS/QR timestamps. Includes a 10-min grace period; late checkout reduces punctuality score linearly.<br/>"
        "• <b>Cleanliness Match (35%):</b> Direct algorithmic output of the Computer Vision Room Condition Delta evaluation.<br/>"
        "• <b>Identity Trust (20%):</b> 100 points for verified DigiLocker/Aadhaar/Discom accounts; 70 points for unverified profiles.<br/>"
        "• <b>Financial Record (10%):</b> 100 baseline; incurs a -15 point penalty for each formal dispute or unpaid overtime invoice."
    )
    story.append(create_callout_box("Objective Trust Index (OTI) Formulation", formula_text, "#F0FDF4", "#86EFAC", "#166534", body_style))

    # =========================================================================
    # PAGE 5: CONCIERGE, PERSONAS, SECURITY & RELATIONAL DATA ARCHITECTURE
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("Features 9 – 12: Concierge, Personas, Security & Schema", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=c_blue, spaceBefore=1, spaceAfter=6))

    story.append(Paragraph("Feature 9 & 10: LoopBot AI Concierge & In-App Inquiry Dispatch", h2_style))
    story.append(Paragraph(
        "• <b>LoopBot AI Concierge:</b> Embedded multi-turn floating assistant assisting seekers with space recommendations, legal micro-lease explanations, "
        "and advising owners on staging and revenue maximization. Features conversational context memory and automatic heuristic fallback.<br/>"
        "• <b>Direct Inquiry Subsystem:</b> Seekers can submit specific questions (e.g. ceiling clearance, 3-phase power). "
        "The AI engine pre-answers routine questions using verified metadata before notifying the host, resolving 70% of inquiries instantly.",
        body_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("Feature 11 & 12: Interactive Persona Switcher & Platform Security", h2_style))
    story.append(Paragraph(
        "• <b>Dual-Role Persona Switcher:</b> Instant switching between Seeker and Host views for rapid testing and live hackathon demonstrations. "
        "Includes a live in-room session console tracking remaining time, caretaker PIN, GPS distance, and checkout diff triggers.<br/>"
        "• <b>Defense-in-Depth Security:</b> Enforces strict input validation, length capping, <code>X-Content-Type-Options: nosniff</code> headers, "
        "IP-based rate limiting on AI routes, and strict boundary delimiters preventing prompt injection attacks.",
        body_style
    ))
    story.append(Spacer(1, 5))

    story.append(Paragraph("4. Relational Data Architecture & Core Models", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=c_blue, spaceBefore=1, spaceAfter=5))

    schema_data = [
        [Paragraph("Model Entity", table_header_style), Paragraph("Primary Schema Attributes", table_header_style), Paragraph("Architectural Responsibility", table_header_style)],
        [
            Paragraph("<b>User</b><br/>(<code>users</code>)", table_cell_bold),
            Paragraph("id, name, email, password_hash, role, is_student_verified, is_aadhaar_verified, is_host_verified, objective_trust_score, discom_provider, upi_vpa_masked", table_cell_style),
            Paragraph("Identity & trust profile. Stores DPDP-compliant masked credentials, NPCI UPI verification status, and calculated OTI scores.", table_cell_style),
        ],
        [
            Paragraph("<b>Space</b><br/>(<code>spaces</code>)", table_cell_bold),
            Paragraph("id, owner_id, title, category, address, latitude, longitude, geofence_radius_meters, physical_access_type, keybox_code, room_qr_token, sqft, price_hourly, ai_lighting, ai_noise_level", table_cell_style),
            Paragraph("Spatial catalog & property metadata. Stores AI-inspected environmental features, printable door QR tokens, and geofencing coordinates.", table_cell_style),
        ],
        [
            Paragraph("<b>Booking</b><br/>(<code>bookings</code>)", table_cell_bold),
            Paragraph("id, space_id, renter_id, start_time, end_time, hours_booked, total_price, status, session_state, arrival_pin, checkin_gps_lat, condition_match_score, escrow_status, micro_lease_agreement", table_cell_style),
            Paragraph("Transaction & telemetry record. Encapsulates synthesized AI micro-lease, session state transitions, GPS coordinates, and escrow refund status.", table_cell_style),
        ],
        [
            Paragraph("<b>Review</b><br/>(<code>reviews</code>)", table_cell_bold),
            Paragraph("id, space_id, user_id, rating, comment, created_at", table_cell_style),
            Paragraph("Subjective qualitative feedback supplementing the objective telemetry calculations.", table_cell_style),
        ],
        [
            Paragraph("<b>SpaceInquiry</b><br/>(<code>space_inquiries</code>)", table_cell_bold),
            Paragraph("id, space_id, user_id, question, ai_answer, created_at", table_cell_style),
            Paragraph("Host-guest inquiry logs with automated AI pre-answers.", table_cell_style),
        ],
    ]
    t_schema = Table(schema_data, colWidths=[105, 205, 194])
    t_schema.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_schema)

    # =========================================================================
    # PAGE 6: UNIT ECONOMICS, MARKET ADVANTAGE & HACKATHON WINNING EDGE
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("5. Unit Economics, Competitive Edge & Hackathon Pitch", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.2, color=c_blue, spaceBefore=1, spaceAfter=6))

    story.append(Paragraph(
        "<b>Market Disruption & Financial Dynamics:</b> Traditional real estate sharing platforms operate with massive operational friction. "
        "<b>SpaceLoop carves a completely new category: Hyper-Local, Zero-Hardware Micro-Utility Rentals</b>. By eliminating hardware capital expenditure (CapEx) "
        "and statutory tenancy friction, SpaceLoop achieves unmatched unit economics:",
        body_style
    ))
    story.append(Spacer(1, 3))

    comp_table_data = [
        [Paragraph("Feature / Vector", table_header_style), Paragraph("Traditional Rental", table_header_style), Paragraph("Coworking Spaces", table_header_style), Paragraph("SpaceLoop Platform", table_header_style)],
        [
            Paragraph("<b>Listing Onboarding</b>", table_cell_bold),
            Paragraph("Manual measurement & broker", table_cell_style),
            Paragraph("Central corporate facility", table_cell_style),
            Paragraph("<b>Instant AI Multimodal Scan</b>", table_cell_style),
        ],
        [
            Paragraph("<b>Contract Type</b>", table_cell_bold),
            Paragraph("11-Month Tenancy Agreement", table_cell_style),
            Paragraph("Monthly Desk Membership", table_cell_style),
            Paragraph("<b>Automated AI Micro-Lease (Sec 52)</b>", table_cell_style),
        ],
        [
            Paragraph("<b>Minimum Booking</b>", table_cell_bold),
            Paragraph("11 Months to 3 Years", table_cell_style),
            Paragraph("1 Full Day to 1 Month", table_cell_style),
            Paragraph("<b>1 Hour Flexible Granularity</b>", table_cell_style),
        ],
        [
            Paragraph("<b>Hardware & Access</b>", table_cell_bold),
            Paragraph("Physical Keys & Lock Changes", table_cell_style),
            Paragraph("RFID Cards & NFC Turnstiles", table_cell_style),
            Paragraph("<b>₹0 Hardware (GPS + Door QR + PIN)</b>", table_cell_style),
        ],
        [
            Paragraph("<b>Identity & Trust</b>", table_cell_bold),
            Paragraph("Paper police verification", table_cell_style),
            Paragraph("ID photocopy on file", table_cell_style),
            Paragraph("<b>DigiLocker + OTI Telemetry</b>", table_cell_style),
        ],
    ]
    t_comp = Table(comp_table_data, colWidths=[110, 130, 130, 134])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_comp)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Unit Economics Breakdown & Host Yields", h2_style))
    story.append(Paragraph(
        "• <b>15% Platform Take-Rate:</b> High gross margin software business model with zero ongoing hardware maintenance overhead.<br/>"
        "• <b>₹0 Host CapEx:</b> Eliminates high upfront costs; a laminated ₹10 printable door QR is the sole physical requirement.<br/>"
        "• <b>Instant ₹100 UPI Escrow Deposit:</b> Protects property owners against trash and power waste while keeping student renter friction near zero.<br/>"
        "• <b>Democratic Urban Access:</b> Delivers quiet, air-conditioned study pods to students at ₹25–₹50/hour while unlocking ₹12,000–₹25,000/month of passive income for urban homeowners.",
        body_style
    ))
    story.append(Spacer(1, 6))

    conclusion_text = (
        "<b>Hack2Ignite 2026 Pitch Summary:</b> SpaceLoop proves that unused urban real estate is not an asset deficit, but a software distribution problem. "
        "By synthesizing Multimodal Spatial AI, India Stack Zero-Hardware Verification, and Automated Micro-Leasing, SpaceLoop creates a liquid, "
        "friction-free marketplace where every square foot has purpose, protection, and passive income potential."
    )
    story.append(create_callout_box("Hack2Ignite 2026 Winning Thesis", conclusion_text, "#F1F5F9", "#CBD5E1", "#0F172A", body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {output_filename}")


if __name__ == "__main__":
    out_file = "SpaceLoop_Complete_Features_Specification.pdf"
    if len(sys.argv) > 1:
        out_file = sys.argv[1]
    generate_spaceloop_pdf(out_file)
