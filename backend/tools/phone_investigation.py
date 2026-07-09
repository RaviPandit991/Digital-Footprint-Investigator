"""Phone number investigation - country, carrier, line type."""
import phonenumbers
from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType

TYPE_NAMES = {
    PhoneNumberType.MOBILE: "Mobile",
    PhoneNumberType.FIXED_LINE: "Fixed line",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed or Mobile",
    PhoneNumberType.TOLL_FREE: "Toll free",
    PhoneNumberType.PREMIUM_RATE: "Premium rate",
    PhoneNumberType.SHARED_COST: "Shared cost",
    PhoneNumberType.VOIP: "VoIP",
    PhoneNumberType.PERSONAL_NUMBER: "Personal",
    PhoneNumberType.PAGER: "Pager",
    PhoneNumberType.UAN: "UAN",
    PhoneNumberType.VOICEMAIL: "Voicemail",
    PhoneNumberType.UNKNOWN: "Unknown",
}


def run(target: str) -> dict:
    number = (target or "").strip()
    if not number:
        return {"error": "Phone number required."}
    if not number.startswith("+"):
        return {"error": "Include country code (e.g. +1 202-555-0123)."}

    try:
        parsed = phonenumbers.parse(number, None)
    except phonenumbers.NumberParseException as e:
        return {"error": f"Parse failed: {e}"}

    valid = phonenumbers.is_valid_number(parsed)
    possible = phonenumbers.is_possible_number(parsed)

    return {
        "target": number,
        "valid": valid,
        "possible": possible,
        "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
        "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
        "country_code": parsed.country_code,
        "region": geocoder.description_for_number(parsed, "en"),
        "carrier": carrier.name_for_number(parsed, "en"),
        "line_type": TYPE_NAMES.get(number_type(parsed), "Unknown"),
        "timezones": list(timezone.time_zones_for_number(parsed)),
        "summary": f"{'Valid' if valid else 'Invalid'} | {geocoder.description_for_number(parsed, 'en') or '?'} | "
                   f"{carrier.name_for_number(parsed, 'en') or 'Unknown carrier'}"
    }
