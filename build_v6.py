#!/usr/bin/env python3
"""Derive versions/6.0/taxonomy.json from 7.0 by applying verified reverse deltas.

Run once to produce the 6.0 file, then verify with verify_v6.py against text
extracted from the official v6.0 PDF. Kept in the repository so the derivation is
auditable rather than a one-off edit.
"""
import copy
import json
import os

SRC = "versions/7.0/taxonomy.json"
DST = "versions/6.0/taxonomy.json"

tax = json.load(open(SRC, encoding="utf-8"))
v6 = copy.deepcopy(tax)
dims = v6["dimensions"]

modi = {m["name"]: m for g in dims["modus"]["high_level_classifications"] for m in g["modi"]}
labels = {v["name"]: v for v in dims["labels_tags"]["values"]}
methods = {v["name"]: v for v in dims["method"]["values"]}
groups = {g["name"]: g for g in dims["modus"]["high_level_classifications"]}

# ---------------------------------------------------------------- metadata
v6.update({
    "version": "6.0",
    "published": "2025-06-18",
    "effective_from": "2026-01-01",
})
v6["source_document"]["filename"] = "EBA_20250618_EBA_Fraud_Taxonomy_(Fraud_Type_Categorisation)_v6.0"
v6["version_history"] = [h for h in v6["version_history"] if h["version"] != "7.0"]
v6["changes"] = []          # the 5.0 to 6.0 change set is not transcribed
v6["license"]["copyright"] = "Euro Banking Association (EBA) 2025"

# ------------------------------------------------------- method: Malware
m = methods["Malware"]
m["definition"] = ("'Malware' is short for malicious software and is used as a single term to refer to virus, "
                   "spy ware, worm etc. Malware is designed to cause damage to a stand-alone computer or a "
                   "networked PC. Wherever a malware term is used it means a program which is designed to damage "
                   "your computer and it could refer to either a virus, worm or Trojan Horse.")
m["source_url"] = ("https://www.websecurity.digicert.com/security-topics/"
                   "what-are-malware-viruses-spyware-and-cookies-and-what-differentiates-them")

# ------------------------------------------------------------------ modi
s = modi["Safe account fraud"]
s["definition"] = ("You'll be contacted, usually on the phone by someone claiming to be from your bank's fraud "
                   "department, the police or a regulatory body (...). They'll say your account has been "
                   "compromised in some way and encourage you to transfer all your money from your bank to a "
                   "'safe account' they control. Alternatively/additionally, this modus could result in the victim "
                   "handing over account credentials or a physical/virtual card or card details and/or completing "
                   "authentication steps required to access the account and/or sign off payment transactions.")
s["source"] = "Moneyhelper Types of Scams"

a = modi["Advance fee fraud"]
a["definition"] = ("Advance fee fraud is when fraudsters target victims to make advance or upfront payments for "
                   "goods, services and/or financial gains that do not materialise. "
                   "Alternatively/additionally, this modus could result in the victim handing over account "
                   "credentials or a physical/virtual card or card details and/or completing authentication steps "
                   "required to access the account and/or sign off payment transactions.")
a["source"] = "National Fraud & Cyber Crime Reporting Centre 'Advance Fee Fraud'"
a["source_url"] = "https://www.actionfraud.police.uk/a-z-of-fraud/advance-fee-fraud"
a.pop("last_modified_in", None); a.pop("last_change_type", None); a.pop("note", None)

modi["Investment fraud"]["source"] = "National Anti-Scam Centre 'Investment scams'"
modi["Extortion"]["source"] = "National Anti-Scam Centre 'Threats and extortion scams'"
modi["Pure account takeover"]["definition"] = modi["Pure account takeover"]["definition"].replace(
    "a fraudster or cyber criminal poses", "a fraudster or computer criminal poses")

groups["Please help"]["definition"] = (
    "Fraudster creates an emotional bond with the victim, typically friendship/sympathy/romantic, then exploits "
    "the bond by getting the victim to help the fraudster financially. Alternatively, the fraudster invents an "
    "emergency scenario requiring the victim to provide financial assistance to a family member or friend.")

# 'Please help' held a single modus in 6.0
ph = groups["Please help"]
ph["modi"] = [{
    "name": "Emotional manipulation",
    "code": "D024",
    "group_code": ph["code"],
    "status": "active",
    "introduced_in": "<=6.0",
    "definition": ("Emotional manipulation is considered to be the ability to influence another individual's "
                   "feelings and behaviors for one's own self-interest or benefit. The victim is tricked into "
                   "providing, for example, money or gifts. Alternatively/additionally, this modus could result in "
                   "the victim handing over account credentials or a physical/virtual card or card details and/or "
                   "completing authentication steps required to access the account and/or sign off payment "
                   "transactions."),
    "source": "Hyde, J. & Grieve, R. (2014). Able and willing: Refining the measurement of emotional manipulation",
    "source_url": "https://www.sciencedirect.com/science/article/abs/pii/S0191886914001408?via%3Dihub",
    "possible_labels_tags": ["Family emergency", "Impersonation", "Romance fraud", "Shock calls"],
    "possible_labels_tags_note": "The v6.0 PDF lists this label as 'Shock call'; the labels/tags section of the same document spells it 'Shock calls'. Normalised to the labels/tags spelling.",
    "abridged": True,
}]
dims["modus"]["retired"] = []

# ---------------------------------------------------------------- labels
for gone in ["Card chip relay", "Money muling", "Money mule victim"]:
    dims["labels_tags"]["values"] = [v for v in dims["labels_tags"]["values"] if v["name"] != gone]
labels = {v["name"]: v for v in dims["labels_tags"]["values"]}

c = labels["CEO fraud"]
c["definition"] = ("CEO fraud will typically start with an email being sent from a fraudster to a member of staff "
                   "in a company's finance department. The member of staff will be told by the fraudster who is "
                   "purporting to be a company director or CEO that they need to quickly transfer money to a "
                   "certain bank account for a specific reason. The member of staff will do as their boss has "
                   "instructed, only to find that they have sent money to a fraudster's bank account. The fraudster "
                   "will normally redistribute this money into other mule accounts and then close down the bank "
                   "account to make it untraceable.")
c["source"] = "National Fraud & Cyber Crime Reporting Centre 'Action Fraud warning after serious rise in CEO fraud'"
c["source_url"] = "https://www.actionfraud.police.uk/alert/action-fraud-warning-after-serious-rise-in-ceo-fraud"
c.pop("last_modified_in", None); c.pop("last_change_type", None); c.pop("note", None)

fb = labels["Fake betting"]
fb["definition"] = ("These scams are a form of gambling made to look like real investments. (...) Betting "
                    "syndicates: The scammer asks you to become a member of a betting syndicate for a joining fee. "
                    "(...) You are required to make ongoing deposits to maintain the balance of the account. The "
                    "scammer tells you that they will use funds in the account to place bets on behalf of the "
                    "syndicate. You, and other 'syndicate members' are promised a percentage of the profits.")
fb["source"] = "National Anti-Scam Centre 'Investment scams / Gambling and sports betting scams'"
fb["source_url"] = "https://www.scamwatch.gov.au/types-of-scams/investment-scams"
fb.pop("last_modified_in", None); fb.pop("last_change_type", None); fb.pop("note", None)

fcs = labels["Fake customer support"]
fcs["definition"] = ("Fraudster impersonates customer support. The scammer will phone you and pretend to be a staff "
                     "member from a large telecommunications or computer company (...). Alternatively they may "
                     "claim to be from a technical support service provider. They will tell you that your computer "
                     "has been sending error messages or that it has a virus. (...) The caller will request remote "
                     "access to your computer to 'find out what the problem is'. The scammer may try to talk you "
                     "into buying unnecessary software or a service to 'fix' the computer, or they may ask you for "
                     "your personal details and your bank or credit card details.")
fcs["source"] = "National Anti-Scam Centre 'Remote access scams'"
fcs["source_url"] = ("https://www.scamwatch.gov.au/protect-yourself/attempts-to-gain-your-personal-information/"
                     "remote-access-scams")
fcs.pop("last_modified_in", None); fcs.pop("last_change_type", None); fcs.pop("note", None)

labels["Beneficiary account change"]["source_url"] = (
    "https://www.citibank.com/tts/sa/emea_marketing/docs/Beneficiary-Change-Request-Risks-and-Best-Practices.pdf")
labels["Card skimming"]["source"] = "FBI 'Scams and Safety'"
labels["Gift card"]["source"] = "National Anti-Scam Centre 'Payment demanded by gift card? It's a scam'"
labels["Goods not received"]["source"] = "National Anti-Scam Centre \"'Tis the season for online shopping scams\""
labels["Sextortion"]["source"] = "National Anti-Scam Centre 'Gen Z the fastest growing victims of scams'"
labels["Social media compromise"].pop("source", None)
labels["Fraudulent use of Contract for Difference (CFD)"]["definition"] = (
    "Contracts for difference (CFD) are a popular way of trading on the price of stocks and indices, commodities, "
    "forex and cryptocurrencies without owning the underlying assets. (...) A CFD is a contract between a broker "
    "and a trader who agree to exchange the difference in value of an underlying security between the beginning "
    "and the end of the contract, often less than one day.")

# 'Romance fraud' was a label in 6.0; it became a modus in 7.0
dims["labels_tags"]["values"].append({
    "name": "Romance fraud",
    "code": "L068",
    "status": "active",
    "introduced_in": "<=6.0",
    "definition": ("Scammers use dating or friendship to win your trust and get your money. Scammers use social "
                   "media, dating or gaming apps and websites to find people looking for love and friendship. They "
                   "create fake profiles, sometimes of famous people. They might also call or message a lot to make "
                   "you feel special. This is sometimes called 'love bombing'. Once you trust them, they might tell "
                   "you about an urgent problem they need your money for. They might ask you to set up accounts or "
                   "transfer money they give you. Or they might convince you to use cryptocurrency and invest in a "
                   "fake scheme they say is real. Either way, the scammer steals your money and disappears, and you "
                   "don't get it back."),
    "source": "National Anti-Scam Centre 'Romance scams'",
    "source_url": "https://www.scamwatch.gov.au/types-of-scams/romance-scams",
    "abridged": True,
    "became_modus_in": {"version": "7.0", "code": "D009",
                        "note": "Moved from labels/tags to the modus section in 7.0. Its definition and cited URL "
                                "also changed at that point (romance-scams became relationship-scams)."},
})
dims["labels_tags"]["values"].sort(key=lambda v: v["name"].lower())
dims["labels_tags"].pop("spelling_note", None)

v6["lifecycle_note"] = (
    "This is the 6.0 snapshot, transcribed in the same shape as 7.0. Codes are shared across versions: an entry "
    "keeps the same code in every version it appears in. Entries present here but not in 7.0 appear in 7.0 under "
    "dimensions.<name>.retired. introduced_in is '<=6.0' throughout because the versions before 6.0 have not been "
    "transcribed; it does not mean the entry was introduced in 6.0.")
for key in ["compatibility", "codes_design_note", "definitions_note", "change_types",
            "review_and_updating_process"]:
    v6.setdefault(key, tax.get(key))

os.makedirs(os.path.dirname(DST), exist_ok=True)
with open(DST, "w", encoding="utf-8") as f:
    json.dump(v6, f, indent=2, ensure_ascii=False)
    f.write("\n")

n_modi = sum(len(g["modi"]) for g in dims["modus"]["high_level_classifications"])
print(f"wrote {DST}: methods={len(dims['method']['values'])} modi={n_modi} "
      f"labels={len(dims['labels_tags']['values'])} instruments={len(dims['payment_instrument']['values'])}")
