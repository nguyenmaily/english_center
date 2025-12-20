"""
Utility functions for user-related operations
"""
from decimal import Decimal


def convert_ielts_to_toeic(ielts_score):
    """
    Convert IELTS score to TOEIC score
    Based on common conversion tables:
    - IELTS 9.0 = TOEIC 990
    - IELTS 8.5 = TOEIC 945
    - IELTS 8.0 = TOEIC 900
    - IELTS 7.5 = TOEIC 850
    - IELTS 7.0 = TOEIC 800
    - IELTS 6.5 = TOEIC 750
    - IELTS 6.0 = TOEIC 700
    - IELTS 5.5 = TOEIC 650
    - IELTS 5.0 = TOEIC 600
    - IELTS 4.5 = TOEIC 550
    - IELTS 4.0 = TOEIC 500
    
    Formula: TOEIC = (IELTS - 1) * 100 + 400
    But with some adjustments for accuracy
    """
    if ielts_score is None:
        return None
    
    ielts = float(ielts_score)
    
    # Conversion table based on common standards
    conversion_map = {
        9.0: 990,
        8.5: 945,
        8.0: 900,
        7.5: 850,
        7.0: 800,
        6.5: 750,
        6.0: 700,
        5.5: 650,
        5.0: 600,
        4.5: 550,
        4.0: 500,
        3.5: 450,
        3.0: 400,
        2.5: 350,
        2.0: 300,
        1.5: 250,
        1.0: 200,
        0.5: 150,
        0.0: 100
    }
    
    # Check exact match first
    if ielts in conversion_map:
        return Decimal(str(conversion_map[ielts]))
    
    # Linear interpolation for values between points
    # Find the two closest points
    sorted_scores = sorted(conversion_map.keys(), reverse=True)
    
    for i in range(len(sorted_scores) - 1):
        if sorted_scores[i] >= ielts >= sorted_scores[i + 1]:
            lower_score = sorted_scores[i]
            upper_score = sorted_scores[i + 1]
            lower_toeic = conversion_map[lower_score]
            upper_toeic = conversion_map[upper_score]
            
            # Linear interpolation
            ratio = (ielts - lower_score) / (upper_score - lower_score)
            toeic = lower_toeic + (upper_toeic - lower_toeic) * ratio
            return Decimal(str(round(toeic)))
    
    # If score is above 9.0, return 990
    if ielts > 9.0:
        return Decimal('990')
    
    # If score is below 0.0, return 100
    if ielts < 0.0:
        return Decimal('100')
    
    return None


def convert_ielts_skill_to_toeic(ielts_skill_score):
    """
    Convert IELTS skill score (0-9) to TOEIC skill score
    For individual skills, we use a similar conversion
    """
    if ielts_skill_score is None:
        return None
    
    ielts = float(ielts_skill_score)
    
    # For individual skills, use similar conversion
    # TOEIC Listening/Reading: 5-495 each
    # TOEIC Speaking/Writing: 0-200 each
    
    # For Listening/Reading (0-495 scale)
    if ielts <= 0:
        return Decimal('5')
    elif ielts >= 9:
        return Decimal('495')
    else:
        # Linear conversion: IELTS 0-9 -> TOEIC 5-495
        toeic = 5 + (ielts / 9) * 490
        return Decimal(str(round(toeic)))
    
    return None


def convert_certificate_scores_to_toeic(certificate_type, reading=None, listening=None, speaking=None, writing=None, total_score=None):
    """
    Convert certificate scores to TOEIC equivalent scores
    Returns dict with toeic_reading, toeic_listening, toeic_speaking, toeic_writing, toeic_total
    """
    result = {
        'toeic_reading': None,
        'toeic_listening': None,
        'toeic_speaking': None,
        'toeic_writing': None,
        'toeic_total': None
    }
    
    if certificate_type == 'toeic':
        # Already TOEIC, return as is
        result['toeic_reading'] = Decimal(str(reading)) if reading else None
        result['toeic_listening'] = Decimal(str(listening)) if listening else None
        result['toeic_speaking'] = Decimal(str(speaking)) if speaking else None
        result['toeic_writing'] = Decimal(str(writing)) if writing else None
        result['toeic_total'] = Decimal(str(total_score)) if total_score else None
    
    elif certificate_type == 'ielts':
        # Convert IELTS to TOEIC
        # For IELTS, reading and listening are typically combined in TOEIC
        # Speaking and writing are separate
        
        # Convert individual skills
        if reading is not None:
            result['toeic_reading'] = convert_ielts_skill_to_toeic(reading)
        if listening is not None:
            result['toeic_listening'] = convert_ielts_skill_to_toeic(listening)
        if speaking is not None:
            # TOEIC Speaking: 0-200 scale
            toeic_speaking = (float(speaking) / 9) * 200
            result['toeic_speaking'] = Decimal(str(round(toeic_speaking)))
        if writing is not None:
            # TOEIC Writing: 0-200 scale
            toeic_writing = (float(writing) / 9) * 200
            result['toeic_writing'] = Decimal(str(round(toeic_writing)))
        
        # Convert total score
        if total_score is not None:
            result['toeic_total'] = convert_ielts_to_toeic(total_score)
        elif reading is not None and listening is not None:
            # Calculate average of reading and listening for TOEIC total
            avg_ielts = (float(reading) + float(listening)) / 2
            result['toeic_total'] = convert_ielts_to_toeic(avg_ielts)
    
    elif certificate_type == 'toefl':
        # TOEFL to TOEIC conversion
        # TOEFL: 0-120 total, 0-30 per skill
        if total_score is not None:
            # Rough conversion: TOEFL 120 = TOEIC 990, TOEFL 0 = TOEIC 100
            toeic_total = 100 + (float(total_score) / 120) * 890
            result['toeic_total'] = Decimal(str(round(toeic_total)))
        
        # Convert individual skills
        if reading is not None:
            toeic_reading = 5 + (float(reading) / 30) * 490
            result['toeic_reading'] = Decimal(str(round(toeic_reading)))
        if listening is not None:
            toeic_listening = 5 + (float(listening) / 30) * 490
            result['toeic_listening'] = Decimal(str(round(toeic_listening)))
        if speaking is not None:
            toeic_speaking = (float(speaking) / 30) * 200
            result['toeic_speaking'] = Decimal(str(round(toeic_speaking)))
        if writing is not None:
            toeic_writing = (float(writing) / 30) * 200
            result['toeic_writing'] = Decimal(str(round(toeic_writing)))
    
    return result

