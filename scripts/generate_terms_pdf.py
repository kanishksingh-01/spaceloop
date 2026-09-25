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
        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "SPACELOOP TECHNOLOGIES // PLATFORM TERMS OF SERVICE & REVERSIBLE LICENSE")
            self.setFont("Helvetica", 7)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(612 - 54, 750, "DOCUMENT ID: SL-DOC-TOS-2026-V2 // STATUTORY COMPLIANCE")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 42, 612 - 54, 42)
        
        self.setFont("Helvetica-Bold", 7)
        self.setFillColor(colors.HexColor("#0F172A"))
        self.drawString(54, 30, "SpaceLoop Platform Agreement")
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(180, 30, "— DPDP Act 2023 / Indian Easements Act 1882 / Model Tenancy Act Compliant")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 30, page_str)
        self.restoreState()


def create_callout_box(title, text, bg_color="#F8FAFC", border_color="#CBD5E1", title_color="#0F172A", body_style=None):
    content = []
    if title:
        content.append(Paragraph(f"<b>{title}</b>", ParagraphStyle(
            'CalloutTitle_' + title[:12].replace(' ', '_').replace(':', ''),
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11,
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


def generate_terms_pdf(output_filename="SpaceLoop_Terms_and_Conditions.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0F172A")
    c_indigo = colors.HexColor("#4F46E5")
    c_blue = colors.HexColor("#2563EB")
    c_text = colors.HexColor("#334155")
    c_muted = colors.HexColor("#64748B")
    c_border = colors.HexColor("#E2E8F0")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=c_muted,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=c_primary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=c_indigo,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=c_text,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    meta_label = ParagraphStyle(
        'MetaLabel',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=c_muted
    )

    meta_val = ParagraphStyle(
        'MetaVal',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=c_primary
    )

    table_header_style = ParagraphStyle(
        'THStyle',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TDStyle',
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=c_text
    )

    story = []

    # ==========================================
    # HEADER & METADATA BLOCK
    # ==========================================
    story.append(Paragraph("SpaceLoop Master Platform Terms of Service", title_style))
    story.append(Paragraph("Standard Peer-to-Peer Temporary Space Use License Agreement & Operations Protocol", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_indigo, spaceBefore=0, spaceAfter=8))

    meta_data = [
        [
            Paragraph("DOCUMENT IDENTIFIER", meta_label),
            Paragraph("EFFECTIVE DATE", meta_label),
            Paragraph("JURISDICTION & LAW", meta_label),
            Paragraph("PLATFORM CLASSIFICATION", meta_label)
        ],
        [
            Paragraph("SL-DOC-TOS-2026-V2", meta_val),
            Paragraph("September 25, 2026", meta_val),
            Paragraph("Republic of India // IT Act 2000", meta_val),
            Paragraph("Technology Intermediary (Sec 79)", meta_val)
        ]
    ]
    t_meta = Table(meta_data, colWidths=[126, 126, 126, 126])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # PREAMBLE CALLOUT
    story.append(create_callout_box(
        "IMPORTANT LEGAL NOTICE — BINDING TEMPORARY LICENSE (NOT A TENANCY):",
        "By creating an account, publishing a space listing, booking a room, or accessing any SpaceLoop premises, "
        "you unconditionally agree to be bound by these Terms. <b>Access granted through SpaceLoop constitutes a temporary, "
        "revocable license under Section 52 of the Indian Easements Act, 1882. It does NOT create any tenancy, leasehold estate, "
        "or possessory rights under the Transfer of Property Act, 1882 or state rent control legislation.</b>",
        bg_color="#FEF2F2", border_color="#FECACA", title_color="#991B1B", body_style=body_style
    ))
    story.append(Spacer(1, 10))

    # ==========================================
    # SECTION 1: PREAMBLE & PLATFORM ROLE
    # ==========================================
    story.append(Paragraph("1. Preamble & Nature of SpaceLoop Platform", h1_style))
    story.append(Paragraph(
        "<b>1.1 Platform Role:</b> SpaceLoop Technologies (\"SpaceLoop\", \"we\", \"us\", or \"our\") operates an online peer-to-peer "
        "technology marketplace facilitating the discovery, booking, physical dual-handshake access, and condition-based micro-escrow "
        "clearance for underutilized physical spaces (\"Spaces\"). SpaceLoop acts strictly as a technology intermediary as defined under "
        "Section 2(1)(w) of the Information Technology Act, 2000, and claims safe harbor protections under Section 79 thereof.",
        body_style
    ))
    story.append(Paragraph(
        "<b>1.2 Independent Contracting Parties:</b> SpaceLoop is not a real estate broker, leasing agent, insurer, property manager, "
        "or bailee. Hosts are independent custodians or owners of the spaces listed. Seekers (\"Guests\") contract directly with Hosts "
        "under the automated Micro-Lease License Agreement synthesized by the platform.",
        body_style
    ))

    # ==========================================
    # SECTION 2: DEFINITIONS
    # ==========================================
    story.append(Paragraph("2. Definitional Framework", h1_style))
    defs = [
        ("Host", "The verified legal owner or authorized custodian listing a physical space on SpaceLoop."),
        ("Seeker / Guest", "The verified registered individual or organizational representative reserving a Space."),
        ("Micro-Lease", "The algorithmic plain-language Temporary Space Use License Agreement generated for each booking."),
        ("Micro-Escrow", "The mandatory ₹100 refundable financial security deposit held in trust during active reservations."),
        ("Dual-Handshake", "The cryptographic physical access validation requiring 50m GPS Geofence + Dynamic QR / PIN."),
        ("OTI Index", "The Objective Telemetry Index (0–100%) tracking punctuality, room condition, and verified KYC compliance.")
    ]
    for term, definition in defs:
        story.append(Paragraph(f"• <b>{term}:</b> {definition}", bullet_style))
    story.append(Spacer(1, 6))

    # ==========================================
    # SECTION 3: LEGAL CHARACTERIZATION (LICENSE NOT TENANCY)
    # ==========================================
    story.append(Paragraph("3. Grant of Revocable License (Absolute Exclusion of Tenancy)", h1_style))
    story.append(Paragraph(
        "<b>3.1 Nature of Grant:</b> The Host grants to the Seeker a limited, revocable, non-exclusive, non-transferable license "
        "to enter and occupy the designated Space solely for the permitted activity, duration, and maximum attendee capacity specified "
        "in the Booking confirmation.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3.2 Exclusion of Tenancy & Sublicensing:</b> The Seeker acknowledges and agrees that: (a) this Agreement does not create any "
        "tenancy, leasehold interest, or statutory occupancy rights; (b) the Seeker acquires no right to quiet enjoyment or exclusive "
        "possession beyond the authorized hours; (c) the Seeker shall not assign, sublet, or grant secondary licenses to any third party; "
        "and (d) upon expiration or termination of the booking duration, the Seeker shall immediately vacate the premise.",
        body_style
    ))
    story.append(Paragraph(
        "<b>3.3 Revocation & Summary Eviction:</b> The Host or SpaceLoop reserves the right to immediately revoke the license and require "
        "immediate departure if the Seeker: exceeds capacity limits, causes nuisance or noise > 75 dB, engages in unlawful conduct, "
        "or refuses electrical appliance shut-down upon check-out.",
        body_style
    ))
    story.append(Spacer(1, 6))

    # ==========================================
    # SECTION 4: IDENTITY VERIFICATION & DATA PRIVACY
    # ==========================================
    story.append(Paragraph("4. Identity Verification, KYC & Data Protection (DPDP Act 2023)", h1_style))
    story.append(Paragraph(
        "<b>4.1 DigiLocker Aadhaar e-KYC:</b> To protect community safety, all Seekers must complete tokenized Aadhaar identity verification. "
        "In strict compliance with Section 8 of the Digital Personal Data Protection Act, 2023 (DPDP Act), <b>SpaceLoop never stores raw "
        "12-digit Aadhaar numbers</b>. Credentials are authenticated via DigiLocker OTP, converted into a one-way salted SHA-256 token "
        "hash, and displayed solely in masked format (XXXX-XXXX-4821).",
        body_style
    ))
    story.append(Paragraph(
        "<b>4.2 Academic Verification:</b> Student and researcher subsidies require validation via institutional domain email (.ac.in or .edu.in) "
        "and masked student identification. Subsidized bookings are strictly non-transferable to non-student third parties.",
        body_style
    ))
    story.append(Paragraph(
        "<b>4.3 Host Premise Proof:</b> Hosts must verify physical premise custody by submitting an active state electricity distribution company "
        "(Discom) Consumer Account (CA) number and completing a verified ₹1 UPI Penny Drop bank match.",
        body_style
    ))

    # ==========================================
    # SECTION 5: FINANCIAL TERMS & ESCROW PROTOCOL
    # ==========================================
    story.append(Paragraph("5. Financial Terms, Pricing & Micro-Escrow Protocol", h1_style))
    
    fee_data = [
        [Paragraph("FINANCIAL COMPONENT", table_header_style), Paragraph("RATE / VALUE", table_header_style), Paragraph("OPERATIONAL RULES & REFUND POLICY", table_header_style)],
        [Paragraph("Space Hourly Subtotal", table_cell_style), Paragraph("₹10 – ₹5,000 / hr", table_cell_style), Paragraph("Determined by Host with dynamic AI pricing recommendations.", table_cell_style)],
        [Paragraph("Platform Service Fee", table_cell_style), Paragraph("5.0% of Rental", table_cell_style), Paragraph("Retained by SpaceLoop to cover infrastructure, KYC, and security.", table_cell_style)],
        [Paragraph("Security Micro-Escrow", table_cell_style), Paragraph("₹100.00 Fixed", table_cell_style), Paragraph("Locked in platform escrow; automatically released upon cleared exit scan.", table_cell_style)],
        [Paragraph("Overstay Surcharge", table_cell_style), Paragraph("150% Prorated Rate", table_cell_style), Paragraph("Applied automatically if checkout occurs > 15 minutes past end time.", table_cell_style)]
    ]
    t_fee = Table(fee_data, colWidths=[130, 94, 280])
    t_fee.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_fee)
    story.append(Spacer(1, 6))

    story.append(Paragraph(
        "<b>5.1 Automated Micro-Escrow Hold:</b> Every reservation requires a ₹100 UPI Micro-Escrow deposit. This deposit is held "
        "in an authorized escrow pool and acts as real-time damage mitigation and electrical shut-off security.",
        body_style
    ))
    story.append(Paragraph(
        "<b>5.2 Instant Escrow Release:</b> Upon departure, if the AI Computer Vision room delta confirms condition match $\ge 90\%$ "
        "and affirmative electrical appliance shut-off, the ₹100 deposit is instantly released via UPI payout rails.",
        body_style
    ))

    # ==========================================
    # SECTION 6: PHYSICAL ACCESS & GEOFENCE PROTOCOL
    # ==========================================
    story.append(Paragraph("6. Physical Access Handshake & Premise Rules", h1_style))
    story.append(Paragraph(
        "<b>6.1 Dual-Handshake Check-In:</b> Physical access requires satisfying two cryptographic checks: (1) Device GPS coordinates "
        "must resolve within a 50-meter Haversine radius of the property; and (2) The Seeker must scan the host's dynamic Room QR Code "
        "or enter the rotating 4-digit Caretaker PIN. Remote or spoofed check-in attempts trigger immediate security cancellation.",
        body_style
    ))
    story.append(Paragraph(
        "<b>6.2 Permitted Use & Activity Constraints:</b> Spaces may only be used for legal activities explicitly stated during booking "
        "(e.g., creative production, study, quiet coworking). Commercial hazardous manufacturing, explosive materials, narcotics, "
        "open flames, or amplified sound exceeding municipal decibel thresholds are strictly prohibited.",
        body_style
    ))
    story.append(Paragraph(
        "<b>6.3 Maximum Occupancy Limit:</b> The Seeker warrants that attendees shall never exceed `space.max_capacity`. Violations "
        "result in immediate license revocation without refund and forfeiture of the ₹100 escrow deposit.",
        body_style
    ))

    # ==========================================
    # SECTION 7: CHECKOUT & DAMAGE SETTLEMENT
    # ==========================================
    story.append(Paragraph("7. Check-Out Protocol & Computer Vision Room Delta Audit", h1_style))
    story.append(Paragraph(
        "<b>7.1 Departure Condition Audit:</b> Seekers must submit an authentic wide-angle exit photograph before leaving. "
        "Our Computer Vision inspection model evaluates furniture restoration, debris removal, and appliance power status.",
        body_style
    ))
    story.append(Paragraph(
        "<b>7.2 Mandatory Electrical Appliance Off-Switch:</b> Air conditioners, studio lights, high-draw amplifiers, and fans must be "
        "powered off. Leaving appliances running flags a non-conformance event, holding the escrow deposit for utility reconciliation.",
        body_style
    ))
    story.append(Paragraph(
        "<b>7.3 Damage Liability:</b> If physical damage exceeds ₹100, the Host may submit visual evidence within 24 hours. "
        "The Seeker agrees to reimburse the Host for documented repair or replacement costs up to the actual damages assessed.",
        body_style
    ))

    # ==========================================
    # SECTION 8: CANCELLATIONS & REFUND POLICY
    # ==========================================
    story.append(Paragraph("8. Cancellation & Refund Policy", h1_style))
    cancel_rules = [
        ("Seeker Cancellation > 2 Hours Before Start", "100% rental subtotal & ₹100 escrow refunded; 5% platform fee retained."),
        ("Seeker Cancellation < 2 Hours Before Start", "50% rental fee paid to Host for booking freeze; 100% escrow refunded."),
        ("Host Cancellation (Any Time)", "100% total refund to Seeker + ₹150 platform credit; Host OTI penalty applied."),
        ("Premise Utility Outage (Discom flag)", "Immediate 100% full refund including platform fees with alternative room rebooking.")
    ]
    for trigger, result in cancel_rules:
        story.append(Paragraph(f"• <b>{trigger}:</b> {result}", bullet_style))
    story.append(Spacer(1, 6))

    # ==========================================
    # SECTION 9: REPUTATION & OTI INDEX
    # ==========================================
    story.append(Paragraph("9. Objective Telemetry Index (OTI) & Reputation Integrity", h1_style))
    story.append(Paragraph(
        "SpaceLoop rejects biased, retaliatory star reviews. User trust is calculated mathematically from verified telemetry: "
        "<b>OTI = (35% Punctuality) + (35% Cleanliness Match) + (20% KYC Status) + (10% Zero-Dispute Record)</b>. "
        "Users whose OTI drops below 70% face temporary booking restrictions or suspension.",
        body_style
    ))

    # ==========================================
    # SECTION 10: LIMITATION OF LIABILITY
    # ==========================================
    story.append(Paragraph("10. Limitation of Liability & Disclaimers", h1_style))
    story.append(Paragraph(
        "<b>10.1 \"As-Is\" Marketplace:</b> To the maximum extent permitted under applicable Indian law, SpaceLoop disclaims all "
        "warranties regarding space suitability, structural safety, third-party conduct, or utility disruptions. "
        "Hosts and Seekers transact at their own risk.",
        body_style
    ))
    story.append(Paragraph(
        "<b>10.2 Liability Cap:</b> Under no circumstances shall SpaceLoop's cumulative liability arising out of any booking exceed "
        "<b>the platform service fees actually earned by SpaceLoop on that specific transaction (typically 5%)</b>.",
        body_style
    ))

    # ==========================================
    # SECTION 11: DISPUTE RESOLUTION & ARBITRATION
    # ==========================================
    story.append(Paragraph("11. Governing Law & Dispute Arbitration", h1_style))
    story.append(Paragraph(
        "<b>11.1 Governing Law:</b> These Terms shall be construed and governed in accordance with the substantive laws of India.",
        body_style
    ))
    story.append(Paragraph(
        "<b>11.2 Mandatory Two-Tier Dispute Resolution:</b> Any dispute between Host, Seeker, or SpaceLoop shall first be submitted to "
        "SpaceLoop's online conciliation portal for 14 business days. If unresolved, disputes shall be finally referred to binding "
        "arbitration administered in New Delhi, India, in accordance with the <b>Arbitration and Conciliation Act, 1996</b>. "
        "The language of arbitration shall be English.",
        body_style
    ))

    # ==========================================
    # SECTION 12: EXECUTION & DIGITAL CONSENT
    # ==========================================
    story.append(Spacer(1, 8))
    story.append(Paragraph("12. Digital Signature & Statutory Acknowledgment", h1_style))
    story.append(Paragraph(
        "By checking <i>\"I accept the SpaceLoop Platform Terms & Revocable License Agreement\"</i> during registration, listing a space, "
        "or confirming a booking reservation, you execute a legally valid electronic record under Section 10A of the Information "
        "Technology Act, 2000, and confirm your consent to all provisions herein.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # SIGNATURE BLOCK TABLE
    sig_data = [
        [
            Paragraph("<b>FOR HOSTS (LICENSOR)</b>", meta_val),
            Paragraph("<b>FOR SEEKERS (LICENSEE)</b>", meta_val),
            Paragraph("<b>FOR SPACELOOP TECHNOLOGIES</b>", meta_val)
        ],
        [
            Paragraph("Consent executed upon space publishing.<br/>Premise verified via Discom CA meter.<br/>UPI penny drop beneficiary confirmed.", table_cell_style),
            Paragraph("Consent executed upon reservation.<br/>Identity verified via DigiLocker token.<br/>Micro-escrow condition accepted.", table_cell_style),
            Paragraph("Platform Terms Enforced.<br/>Intermediary Safe Harbor Active.<br/>Digital Certificate: #SL-2026-AUTH", table_cell_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[168, 168, 168])
    t_sig.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 0.5, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_sig)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated: {output_filename}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "SpaceLoop_Terms_and_Conditions.pdf"
    generate_terms_pdf(out)
