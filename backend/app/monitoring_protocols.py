"""
Monitoring Protocol Definitions
Defines condition-specific metrics and thresholds for clinical trial monitoring
"""

from typing import Dict, List, Any

MONITORING_PROTOCOLS: Dict[str, Dict[str, Any]] = {
    'CRS': {
        'label': 'Cytokine Release Syndrome',
        'description': 'Monitoring for immune-related adverse events including fever, hypotension, and hypoxia',
        'metrics': [
            'crs_score',                # Overall CRS risk score (facial flushing)
            'heart_rate',               # Elevated HR indicator
            'respiratory_rate',         # Respiratory distress
            'face_touching_frequency',  # Face rubbing (fever, discomfort)
            'restlessness_index'        # Agitation, discomfort
        ],
        'alert_threshold': 0.7,
        'severity_levels': {
            'low': 0.4,
            'moderate': 0.6,
            'high': 0.8
        },
        'keywords': [
            'myeloma', 'lymphoma', 'leukemia', 'car-t', 'bispecific',
            'immunotherapy', 'cytokine', 'bcma', 'cd19', 'cd3'
        ]
    },
    'SEIZURE': {
        'label': 'Seizure Monitoring',
        'description': 'Detection of seizure activity and neurological symptoms',
        'metrics': [
            'tremor_detection',         # Involuntary shaking
            'repetitive_movements',     # Stereotyped movements
            'movement_vigor_spikes',    # Sudden jerking
            'coordination_issues',      # Motor control problems
            'body_position_changes'     # Sudden falls
        ],
        'alert_threshold': 0.7,
        'severity_levels': {
            'low': 0.4,
            'moderate': 0.6,
            'high': 0.8
        },
        'keywords': [
            'epilepsy', 'seizure', 'convulsion', 'neurological',
            'anti-epileptic', 'brain', 'neurology'
        ]
    }
}

def get_protocol(condition: str) -> Dict[str, Any]:
    """Get monitoring protocol configuration for a condition"""
    return MONITORING_PROTOCOLS.get(condition.upper(), None)

def get_all_protocols() -> Dict[str, Dict[str, Any]]:
    """Get all available monitoring protocols"""
    return MONITORING_PROTOCOLS

def recommend_protocols(patient_condition: str) -> List[str]:
    """
    Recommend monitoring protocols based on patient condition text

    Args:
        patient_condition: Patient's condition description

    Returns:
        List of recommended protocol names (e.g., ['CRS', 'SEIZURE'])
    """
    if not patient_condition:
        return []

    condition_lower = patient_condition.lower()
    recommendations = []

    for protocol_name, protocol_config in MONITORING_PROTOCOLS.items():
        # Check if any keywords match the patient condition
        for keyword in protocol_config['keywords']:
            if keyword in condition_lower:
                recommendations.append(protocol_name)
                break  # Don't add same protocol multiple times

    return recommendations

def get_severity_label(protocol: str, score: float) -> str:
    """
    Get severity label for a score

    Args:
        protocol: Protocol name (e.g., 'CRS')
        score: Risk score (0-1)

    Returns:
        Severity label ('low', 'moderate', 'high', 'unknown')
    """
    config = get_protocol(protocol)
    if not config:
        return 'unknown'

    levels = config['severity_levels']
    if score >= levels['high']:
        return 'high'
    elif score >= levels['moderate']:
        return 'moderate'
    elif score >= levels['low']:
        return 'low'
    else:
        return 'minimal'
