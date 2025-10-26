"""
PDF Generation Service for Handoff Forms
Generates professional, formatted PDFs from handoff form data
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.colors import HexColor
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import logging

from app.models.handoff_forms import HandoffFormContent, AlertInfo

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generate professional handoff form PDFs"""

    def __init__(self, output_dir: str = "/tmp/handoff_forms"):
        """
        Initialize PDF generator

        Args:
            output_dir: Directory to save generated PDFs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Define color scheme
        self.primary_color = HexColor("#2563eb")  # Blue
        self.critical_color = HexColor("#dc2626")  # Red
        self.high_color = HexColor("#ea580c")  # Orange
        self.medium_color = HexColor("#ca8a04")  # Yellow
        self.low_color = HexColor("#059669")  # Green
        self.header_bg = HexColor("#f1f5f9")  # Light gray

        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=self.primary_color,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=self.primary_color,
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))

        # Section header
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.black,
            spaceAfter=6,
            spaceBefore=10,
            fontName='Helvetica-Bold',
            backColor=self.header_bg,
            leftIndent=6,
            rightIndent=6
        ))

        # Alert title
        self.styles.add(ParagraphStyle(
            name='AlertTitle',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            spaceAfter=4
        ))

        # Body text
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leading=14
        ))

        # Small text
        self.styles.add(ParagraphStyle(
            name='SmallText',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            spaceAfter=4
        ))

    def _get_severity_color(self, severity: str) -> HexColor:
        """Get color for severity level"""
        severity_map = {
            "critical": self.critical_color,
            "high": self.high_color,
            "medium": self.medium_color,
            "low": self.low_color,
            "info": HexColor("#6b7280")
        }
        return severity_map.get(severity.lower(), colors.grey)

    def generate_handoff_pdf(
        self,
        form_content: HandoffFormContent,
        form_number: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Generate a complete handoff form PDF

        Args:
            form_content: HandoffFormContent object with all form data
            form_number: Unique form number (e.g., "HO-2025-0001")
            filename: Optional custom filename (defaults to form_number.pdf)

        Returns:
            Full path to generated PDF file
        """
        if filename is None:
            filename = f"{form_number}.pdf"

        filepath = os.path.join(self.output_dir, filename)

        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )

        # Build content
        story = []

        # Header
        story.extend(self._build_header(form_number, form_content))
        story.append(Spacer(1, 0.2*inch))

        # Patient Information
        story.extend(self._build_patient_section(form_content))
        story.append(Spacer(1, 0.15*inch))

        # Alert Summary
        story.extend(self._build_alert_summary(form_content))
        story.append(Spacer(1, 0.15*inch))

        # Clinical Context
        if form_content.recent_vitals or form_content.current_treatments:
            story.extend(self._build_clinical_context(form_content))
            story.append(Spacer(1, 0.15*inch))

        # Action Items
        story.extend(self._build_action_items(form_content))
        story.append(Spacer(1, 0.15*inch))

        # Related Alerts
        if form_content.related_alerts:
            story.extend(self._build_related_alerts(form_content))
            story.append(Spacer(1, 0.15*inch))

        # Timeline
        if form_content.timeline:
            story.extend(self._build_timeline(form_content))
            story.append(Spacer(1, 0.15*inch))

        # Footer
        story.extend(self._build_footer(form_content))

        # Build PDF
        doc.build(story)
        logger.info(f"Generated PDF: {filepath}")

        return filepath

    def _build_header(self, form_number: str, content: HandoffFormContent) -> List:
        """Build PDF header"""
        elements = []

        # Title
        elements.append(Paragraph(
            "PATIENT HANDOFF FORM",
            self.styles['CustomTitle']
        ))

        # Form details table
        severity_color = self._get_severity_color(content.severity_level.value)

        header_data = [
            ["Form Number:", form_number, "Severity:", content.severity_level.value.upper()],
            ["Generated:", content.generated_at.strftime("%Y-%m-%d %H:%M UTC"), "Recipient:", content.intended_recipient],
        ]

        header_table = Table(header_data, colWidths=[1.2*inch, 2.3*inch, 1.0*inch, 2.0*inch])
        header_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (3, 0), (3, 0), severity_color),
            ('FONTNAME', (3, 0), (3, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))

        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=2, color=self.primary_color, spaceAfter=0.1*inch))

        return elements

    def _build_patient_section(self, content: HandoffFormContent) -> List:
        """Build patient information section"""
        elements = []
        patient = content.patient_info

        elements.append(Paragraph("PATIENT INFORMATION", self.styles['SectionHeader']))

        patient_data = [
            ["Patient ID:", patient.patient_id or "N/A"],
            ["Name:", patient.name or "N/A"],
            ["Age:", str(patient.age) if patient.age else "N/A"],
            ["Room:", patient.room_number or "N/A"],
            ["Diagnosis:", patient.diagnosis or "N/A"],
            ["Treatment Status:", patient.treatment_status or "N/A"],
        ]

        if patient.allergies:
            allergies_text = ", ".join(patient.allergies)
            patient_data.append(["<b>Allergies:</b>", f"<font color='red'>{allergies_text}</font>"])

        patient_table = Table(patient_data, colWidths=[1.5*inch, 5.0*inch])
        patient_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (1, 0), (1, -1), 10),
        ]))

        elements.append(patient_table)
        return elements

    def _build_alert_summary(self, content: HandoffFormContent) -> List:
        """Build alert summary section"""
        elements = []

        elements.append(Paragraph("ALERT SUMMARY", self.styles['SectionHeader']))

        # Primary concern (highlighted)
        concern_text = f"<font color='{self._get_severity_color(content.severity_level.value)}'><b>{content.primary_concern}</b></font>"
        elements.append(Paragraph(concern_text, self.styles['AlertTitle']))

        # Detailed summary
        elements.append(Paragraph(content.alert_summary, self.styles['BodyText']))

        return elements

    def _build_clinical_context(self, content: HandoffFormContent) -> List:
        """Build clinical context section"""
        elements = []

        elements.append(Paragraph("CLINICAL CONTEXT", self.styles['SectionHeader']))

        # Recent vitals
        if content.recent_vitals:
            elements.append(Paragraph("<b>Recent Vital Signs:</b>", self.styles['BodyText']))
            vitals_text = []
            for key, value in content.recent_vitals.items():
                vitals_text.append(f"• {key}: {value}")
            elements.append(Paragraph("<br/>".join(vitals_text), self.styles['BodyText']))

        # Current treatments
        if content.current_treatments:
            elements.append(Paragraph("<b>Current Treatments:</b>", self.styles['BodyText']))
            treatments_text = "<br/>".join([f"• {t}" for t in content.current_treatments])
            elements.append(Paragraph(treatments_text, self.styles['BodyText']))

        # Relevant history
        if content.relevant_history:
            elements.append(Paragraph("<b>Relevant History:</b>", self.styles['BodyText']))
            elements.append(Paragraph(content.relevant_history, self.styles['BodyText']))

        return elements

    def _build_action_items(self, content: HandoffFormContent) -> List:
        """Build action items section"""
        elements = []

        elements.append(Paragraph("RECOMMENDED ACTIONS", self.styles['SectionHeader']))

        # Recommended actions (numbered list)
        for i, action in enumerate(content.recommended_actions, 1):
            elements.append(Paragraph(f"{i}. {action}", self.styles['BodyText']))

        # Urgency notes
        if content.urgency_notes:
            elements.append(Spacer(1, 0.1*inch))
            urgency_text = f"<font color='{self.critical_color}'><b>⚠ URGENT: {content.urgency_notes}</b></font>"
            elements.append(Paragraph(urgency_text, self.styles['BodyText']))

        # Protocols to follow
        if content.protocols_to_follow:
            elements.append(Spacer(1, 0.1*inch))
            elements.append(Paragraph("<b>Protocols to Follow:</b>", self.styles['BodyText']))
            protocols_text = "<br/>".join([f"• {p}" for p in content.protocols_to_follow])
            elements.append(Paragraph(protocols_text, self.styles['BodyText']))

        return elements

    def _build_related_alerts(self, content: HandoffFormContent) -> List:
        """Build related alerts section"""
        elements = []

        elements.append(Paragraph("RELATED ALERTS", self.styles['SectionHeader']))

        for alert in content.related_alerts[:5]:  # Limit to 5 most recent
            severity_color = self._get_severity_color(alert.severity.value)
            alert_text = f"<font color='{severity_color}'><b>[{alert.severity.value.upper()}]</b></font> {alert.title}"
            elements.append(Paragraph(alert_text, self.styles['BodyText']))

            if alert.description:
                elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{alert.description}", self.styles['SmallText']))

            time_str = alert.triggered_at.strftime("%Y-%m-%d %H:%M") if alert.triggered_at else "N/A"
            elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;Triggered: {time_str}", self.styles['SmallText']))
            elements.append(Spacer(1, 0.05*inch))

        return elements

    def _build_timeline(self, content: HandoffFormContent) -> List:
        """Build timeline section"""
        elements = []

        elements.append(Paragraph("EVENT TIMELINE", self.styles['SectionHeader']))

        for event in content.timeline[:10]:  # Limit to 10 events
            timestamp = event.get("timestamp", "")
            event_type = event.get("event", "")
            details = event.get("details", "")

            event_text = f"<b>{timestamp}</b> - {event_type}"
            elements.append(Paragraph(event_text, self.styles['BodyText']))

            if details:
                elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{details}", self.styles['SmallText']))

        return elements

    def _build_footer(self, content: HandoffFormContent) -> List:
        """Build PDF footer"""
        elements = []

        elements.append(Spacer(1, 0.2*inch))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))

        # Special instructions
        if content.special_instructions:
            elements.append(Paragraph("<b>Special Instructions:</b>", self.styles['BodyText']))
            elements.append(Paragraph(content.special_instructions, self.styles['BodyText']))

        # Contact information
        if content.contact_information:
            elements.append(Paragraph("<b>Contact Information:</b>", self.styles['SmallText']))
            contact_text = " | ".join([f"{k}: {v}" for k, v in content.contact_information.items()])
            elements.append(Paragraph(contact_text, self.styles['SmallText']))

        # Generation info
        footer_text = f"Generated by {content.generated_by} on {content.generated_at.strftime('%Y-%m-%d at %H:%M UTC')}"
        elements.append(Paragraph(footer_text, self.styles['SmallText']))

        return elements


# Create singleton instance
pdf_generator = PDFGenerator()
