"""Public records - generates jurisdiction-specific search URLs."""
from urllib.parse import quote_plus


def run(target: str) -> dict:
    q = (target or "").strip()
    if not q:
        return {"error": "Name or entity required."}

    encoded = quote_plus(q)
    registries = {
        "United States": {
            "SEC EDGAR (companies)":   f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={encoded}&type=&dateb=&owner=include&count=40",
            "OpenCorporates (US)":     f"https://opencorporates.com/companies?q={encoded}&jurisdiction_code=us",
            "PACER (court records)":   f"https://pcl.uscourts.gov/pcl/pages/search/findParty.jsf",
            "USPTO Trademarks":        f"https://tmsearch.uspto.gov/bin/showfield?f=toc&state=4801%3Ajhyk9k.1.1&p_search=searchss&p_L=50&BackReference=&p_plural=yes&p_s_PARA1=&p_tagrepl%7E%3A=PARA1%24LD&expr=PARA1+AND+PARA2&p_s_PARA2={encoded}&p_tagrepl%7E%3A=PARA2%24ALL&p_op_ALL=AND&a_default=search&a_search=Submit+Query&a_search=Submit+Query",
            "USA.gov Data":            f"https://catalog.data.gov/dataset?q={encoded}",
        },
        "United Kingdom": {
            "Companies House":         f"https://find-and-update.company-information.service.gov.uk/search?q={encoded}",
            "UK Court Judgments":      f"https://www.find-case-law.service.gov.uk/judgments/search?query={encoded}",
        },
        "European Union": {
            "OpenCorporates (EU)":     f"https://opencorporates.com/companies?q={encoded}",
            "EU Court of Justice":     f"https://curia.europa.eu/juris/liste.jsf?language=en&td=ALL&num={encoded}",
        },
        "India": {
            "MCA (Ministry of Corporate Affairs)": "https://www.mca.gov.in/mcafoportal/viewCompanyMasterData.do",
            "Supreme Court eCourts":   "https://main.sci.gov.in/",
        },
        "Global": {
            "OpenCorporates (global)": f"https://opencorporates.com/companies?q={encoded}",
            "LittleSis (power maps)":  f"https://littlesis.org/search?q={encoded}",
            "OCCRP Aleph":             f"https://data.occrp.org/search?q={encoded}",
            "OFAC Sanctions":          f"https://sanctionssearch.ofac.treas.gov/",
            "UN Security Council":     f"https://scsanctions.un.org/consolidated",
            "Wikidata":                f"https://www.wikidata.org/w/index.php?search={encoded}",
        },
    }

    return {
        "target": q,
        "registries": registries,
        "note": "Public records access varies by jurisdiction. Some may require CAPTCHA or manual navigation.",
        "summary": f"Generated public record search links across {len(registries)} regions."
    }
