"""
Krude - Reference Data Generator for OFAC and Maritime Headlines
=============================================================================
Generates headlines.csv and ofac.csv reference files for single-database ingestion.
"""

import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent

def build_ofac_csv(output_path: Path = DATA_DIR / "ofac.csv") -> Path:
    """Generates the OFAC sanctions and restricted entities reference table."""
    records = [
        ("OFAC-IR-001", "National Iranian Oil Company (NIOC)", "Iran", "Primary Sanctions", "IRAN-EO13846", 1, 0.0, "Comprehensive SDN sanctions on crude exports and maritime vessels"),
        ("OFAC-IR-002", "National Iranian Tanker Company (NITC)", "Iran", "Maritime Transport", "IRAN-EO13846", 1, 0.0, "Blocked maritime crude carrier fleet"),
        ("OFAC-RU-001", "Rosneft Oil Company", "Russia", "Sectoral / Price Cap", "RUSSIA-EO14024", 1, 60.0, "G7/EU $60/bbl price cap compliance required for Western maritime services"),
        ("OFAC-RU-002", "Sovcomflot (SCF Group)", "Russia", "Maritime SDN", "RUSSIA-EO14024", 1, 60.0, "Designated state tanker operator subject to asset freezes"),
        ("OFAC-RU-003", "Gazprom Neft", "Russia", "Sectoral Sanctions", "RUSSIA-EO14024", 1, 60.0, "Restricted access to Western debt, equity, and deepwater extraction tech"),
        ("OFAC-VE-001", "Petróleos de Venezuela, S.A. (PDVSA)", "Venezuela", "Secondary Sanctions", "VENEZUELA-EO13850", 1, 45.0, "Subject to general licenses GL44A restrictions and crude export limits"),
        ("OFAC-IQ-001", "State Organization for Marketing of Oil (SOMO)", "Iraq", "Unrestricted", "NONE", 0, 0.0, "Authorized national crude marketing entity; unrestricted"),
        ("OFAC-SA-001", "Saudi Aramco", "Saudi Arabia", "Unrestricted", "NONE", 0, 0.0, "National oil company; standard international commercial terms"),
        ("OFAC-AE-001", "Abu Dhabi National Oil Company (ADNOC)", "UAE", "Unrestricted", "NONE", 0, 0.0, "State producer; fully accessible and unrestricted"),
        ("OFAC-KW-001", "Kuwait Petroleum Corporation (KPC)", "Kuwait", "Unrestricted", "NONE", 0, 0.0, "State oil marketer; standard commercial terms"),
        ("OFAC-QA-001", "QatarEnergy", "Qatar", "Unrestricted", "NONE", 0, 0.0, "State energy corporation; unrestricted"),
        ("OFAC-OM-001", "OQ / Petroleum Development Oman", "Oman", "Unrestricted", "NONE", 0, 0.0, "National producer; outside Hormuz transit, unrestricted"),
        ("OFAC-NG-001", "Nigerian National Petroleum Company (NNPC)", "Nigeria", "Unrestricted", "NONE", 0, 0.0, "National producer; unrestricted sweet crude export"),
        ("OFAC-AO-001", "Sonangol", "Angola", "Unrestricted", "NONE", 0, 0.0, "State energy company; unrestricted West African crude"),
        ("OFAC-BR-001", "Petrobras", "Brazil", "Unrestricted", "NONE", 0, 0.0, "National offshore producer; unrestricted"),
        ("OFAC-US-001", "US Gulf Coast Exporters", "USA", "Unrestricted", "NONE", 0, 0.0, "Commercial US export terminals; unrestricted"),
        ("OFAC-LY-001", "National Oil Corporation (NOC)", "Libya", "Unrestricted", "LIBYA-EO13726", 0, 0.0, "Subject to intermittent force majeure monitoring"),
        ("OFAC-GY-001", "ExxonMobil Guyana / Liza Operator", "Guyana", "Unrestricted", "NONE", 0, 0.0, "Offshore deepwater producer; unrestricted"),
        ("OFAC-MX-001", "Petróleos Mexicanos (Pemex)", "Mexico", "Unrestricted", "NONE", 0, 0.0, "National crude producer; unrestricted")
    ]

    cols = ["entity_id", "entity_name", "country", "sanction_type", "program", "sdn_flag", "price_cap_usd_bbl", "notes"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in records:
            w.writerow(r)

    print(f"[OK] Generated OFAC sanctions dataset: {output_path} ({len(records)} entities)")
    return output_path

def build_headlines_csv(output_path: Path = DATA_DIR / "headlines.csv") -> Path:
    """Generates the maritime risk headlines reference table."""
    records = [
        ("HL-001", "2026-08-20T08:30:00Z", "IRGC Fast-Attack Craft Harass Commercial Tankers in Strait of Hormuz", "Lloyd's List Intelligence", "Hormuz", 8.8, "CRITICAL", "Heightened naval patrols north of Oman; Joint War Committee declares Hormuz higher-risk area.", "https://lloydslist.maritimeintelligence.informa.com"),
        ("HL-002", "2026-08-19T14:15:00Z", "Renewed Drone Swarm Attacks Reported on Red Sea Bab-el-Mandeb Approach", "UK Maritime Trade Operations (UKMTO)", "Bab-el-Mandeb", 7.8, "HIGH", "Major tanker operators rerouting via Cape of Good Hope after anti-ship missile activity.", "https://www.ukmto.org"),
        ("HL-003", "2026-08-18T18:00:00Z", "Western Coalition Expands Secondary Sanctions on Shadow Tanker Fleet", "OFAC / S&P Global Commodity Insights", "Suez", 6.2, "MEDIUM", "Flag de-registrations and insurance enforcement delay Russian crude voyages destined for Asia.", "https://home.treasury.gov/policy-issues/financial-sanctions"),
        ("HL-004", "2026-08-17T11:45:00Z", "Malacca Strait Maritime Congestion Reaches Seasonal Peak at Singapore Roads", "Singapore MPA", "Malacca", 2.5, "LOW", "Routine navigational warnings; average wait times increased by 14 hours.", "https://www.mpa.gov.sg"),
        ("HL-005", "2026-08-16T09:20:00Z", "West African Offshore Deepwater Terminals Operate at Full Capacity", "NNPC / TotalEnergies", "Cape of Good Hope", 1.8, "LOW", "Stable loading across Bonny and Nemba FPSO units; open sea transit via Cape unimpeded.", "https://www.nnpcgroup.com"),
        ("HL-006", "2026-08-15T16:10:00Z", "Panama Canal Transits Resume Normal Draft Following Reservoir Recovery", "Panama Canal Authority (ACP)", "Panama", 1.5, "LOW", "Daily booking slots restored to 36 vessels; tolls unchanged.", "https://pancanal.com"),
        ("HL-007", "2026-08-14T12:00:00Z", "East-West Petroline Yanbu Terminal Completes Pumping Station Expansion", "Saudi Aramco", "Hormuz", 3.0, "LOW", "Red Sea export capacity confirmed at 7.0 MBPD offering full Hormuz bypass option.", "https://www.aramco.com"),
        ("HL-008", "2026-08-13T10:30:00Z", "ADCOP Fujairah Deepwater Jetty Berths Very Large Crude Carrier", "ADNOC Onshore", "Hormuz", 2.8, "LOW", "Direct Indian Ocean loading operational at 1.8 MBPD bypass capacity.", "https://www.adnoc.ae")
    ]

    cols = ["id", "timestamp", "headline", "source", "corridor", "risk_score", "severity", "summary", "url"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in records:
            w.writerow(r)

    print(f"[OK] Generated headlines dataset: {output_path} ({len(records)} headlines)")
    return output_path

if __name__ == "__main__":
    build_ofac_csv()
    build_headlines_csv()
