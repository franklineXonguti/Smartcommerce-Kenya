"""
Constants for Kenya-specific data.
"""

# 47 Counties of Kenya
KENYAN_COUNTIES = [
    ('mombasa', 'Mombasa'),
    ('kwale', 'Kwale'),
    ('kilifi', 'Kilifi'),
    ('tana_river', 'Tana River'),
    ('lamu', 'Lamu'),
    ('taita_taveta', 'Taita Taveta'),
    ('garissa', 'Garissa'),
    ('wajir', 'Wajir'),
    ('mandera', 'Mandera'),
    ('marsabit', 'Marsabit'),
    ('isiolo', 'Isiolo'),
    ('meru', 'Meru'),
    ('tharaka_nithi', 'Tharaka Nithi'),
    ('embu', 'Embu'),
    ('kitui', 'Kitui'),
    ('machakos', 'Machakos'),
    ('makueni', 'Makueni'),
    ('nyandarua', 'Nyandarua'),
    ('nyeri', 'Nyeri'),
    ('kirinyaga', 'Kirinyaga'),
    ('muranga', "Murang'a"),
    ('kiambu', 'Kiambu'),
    ('turkana', 'Turkana'),
    ('west_pokot', 'West Pokot'),
    ('samburu', 'Samburu'),
    ('trans_nzoia', 'Trans Nzoia'),
    ('uasin_gishu', 'Uasin Gishu'),
    ('elgeyo_marakwet', 'Elgeyo Marakwet'),
    ('nandi', 'Nandi'),
    ('baringo', 'Baringo'),
    ('laikipia', 'Laikipia'),
    ('nakuru', 'Nakuru'),
    ('narok', 'Narok'),
    ('kajiado', 'Kajiado'),
    ('kericho', 'Kericho'),
    ('bomet', 'Bomet'),
    ('kakamega', 'Kakamega'),
    ('vihiga', 'Vihiga'),
    ('bungoma', 'Bungoma'),
    ('busia', 'Busia'),
    ('siaya', 'Siaya'),
    ('kisumu', 'Kisumu'),
    ('homa_bay', 'Homa Bay'),
    ('migori', 'Migori'),
    ('kisii', 'Kisii'),
    ('nyamira', 'Nyamira'),
    ('nairobi', 'Nairobi'),
]

# Phone number prefixes for validation
KENYAN_PHONE_PREFIXES = [
    '07',  # Safaricom, Airtel
    '01',  # Safaricom, Airtel (alternative)
    '+254',  # International format
]

def validate_kenyan_phone(phone):
    """
    Validate Kenyan phone number format.
    Accepts: 07XXXXXXXX, 01XXXXXXXX, +2547XXXXXXXX, +2541XXXXXXXX
    """
    import re
    
    # Remove spaces and dashes
    phone = re.sub(r'[\s\-]', '', phone)
    
    # Check formats
    if re.match(r'^07\d{8}$', phone):
        return True
    if re.match(r'^01\d{8}$', phone):
        return True
    if re.match(r'^\+2547\d{8}$', phone):
        return True
    if re.match(r'^\+2541\d{8}$', phone):
        return True
    
    return False

def normalize_kenyan_phone(phone):
    """
    Normalize Kenyan phone number to international format (+254XXXXXXXXX).
    """
    import re
    
    # Remove spaces and dashes
    phone = re.sub(r'[\s\-]', '', phone)
    
    # Already in international format
    if phone.startswith('+254'):
        return phone
    
    # Convert 07/01 to +254
    if phone.startswith('07'):
        return '+254' + phone[1:]
    if phone.startswith('01'):
        return '+254' + phone[1:]
    
    return phone
