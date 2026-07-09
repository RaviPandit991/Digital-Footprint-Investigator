"""Phone investigation - carrier, region, line type, OSINT search links."""
import phonenumbers
from phonenumbers import geocoder, carrier, timezone, number_type, PhoneNumberType
from urllib.parse import quote_plus

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


def _osint_links(number: str, e164: str, national: str) -> dict:
    """Build search URLs at popular phone-lookup sites."""
    q = quote_plus(number)
    return {
        "TrueCaller":    f"https://www.truecaller.com/search/us/{q}",
        "WhoCallsMe":    f"https://whocalled.us/lookup/{quote_plus(national.replace(' ', ''))}",
        "SpyDialer":     f"https://www.spydialer.com/default.aspx?phone={q}",
        "Sync.me":       f"https://sync.me/search/?number={q}",
        "NumLookup":     f"https://www.numlookup.com/{quote_plus(e164)}",
        "Google Search": f"https://www.google.com/search?q=%22{q}%22",
        "OpenCNAM":      f"https://api.opencnam.com/v3/phone/{quote_plus(e164)}",
        "BeenVerified":  f"https://www.beenverified.com/rf/search/phone?phone={q}",
    }


def run(target: str, include_osint_links: bool = True) -> dict:
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

    intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    natl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    rfc = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.RFC3966)

    out = {
        "target": number,
        "valid": valid, "possible": possible,
        "international": intl, "national": natl,
        "e164": e164, "rfc3966": rfc,
        "country_code": parsed.country_code,
        "region": geocoder.description_for_number(parsed, "en"),
        "carrier": carrier.name_for_number(parsed, "en"),
        "line_type": TYPE_NAMES.get(number_type(parsed), "Unknown"),
        "timezones": list(timezone.time_zones_for_number(parsed)),
    }

    if include_osint_links:
        out["osint_lookup_links"] = _osint_links(number, e164, natl)

    out["summary"] = (f"{'Valid' if valid else 'Invalid'} | "
                      f"{out['region'] or '?'} | "
                      f"{out['carrier'] or 'Unknown carrier'} | "
                      f"{out['line_type']}")
    return out
