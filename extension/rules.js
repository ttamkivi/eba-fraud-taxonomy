/* Reference rules: phrase patterns with weights, one value each. Deterministic and inspectable.
   Every value returned carries the words of the case that produced it. */
globalThis.EBA_RULES = [
 {
  "dim": "method",
  "value": "Phone contact",
  "w": 3,
  "pats": [
   "\\bcall(?:ed|er|ing)?\\b",
   "\\bphone(?:d| call)\\b",
   "\\brang\\b"
  ]
 },
 {
  "dim": "method",
  "value": "Text message contact",
  "w": 3,
  "pats": [
   "\\btext message\\b",
   "\\bsms\\b",
   "\\btexted?\\b"
  ]
 },
 {
  "dim": "method",
  "value": "Text message contact",
  "w": 8,
  "pats": [
   "text message[^.]{0,80}(?:days|weeks|hours) (?:earlier|before|ago)",
   "(?:days|weeks) (?:earlier|before)[^.]{0,80}text message"
  ]
 },
 {
  "dim": "method",
  "value": "Email contact",
  "w": 3,
  "pats": [
   "\\bemail(?:ed)? (?:from|arrived)\\b",
   "\\ban email\\b",
   "\\bby email\\b"
  ]
 },
 {
  "dim": "method",
  "value": "Social media contact",
  "w": 3,
  "pats": [
   "social media",
   "\\bfacebook\\b",
   "\\binstagram\\b",
   "dating (?:site|app)"
  ]
 },
 {
  "dim": "method",
  "value": "Online contact",
  "w": 2,
  "pats": [
   "(?:met|contacted|approached)[^.]{0,30}\\bonline\\b",
   "\\bwebsite\\b",
   "\\bchat(?:ted)?\\b"
  ]
 },
 {
  "dim": "method",
  "value": "Fake merchant",
  "w": 3,
  "pats": [
   "fake (?:shop|merchant|store|seller)",
   "never (?:arrived|delivered|shipped)"
  ]
 },
 {
  "dim": "method",
  "value": "Fake advertising",
  "w": 3,
  "pats": [
   "\\badvert",
   "\\blisting\\b",
   "saw an ad"
  ]
 },
 {
  "dim": "method",
  "value": "Malware",
  "w": 1,
  "pats": [
   "\\bmalware\\b",
   "remote (?:access|desktop)",
   "anydesk",
   "teamviewer"
  ]
 },
 {
  "dim": "method",
  "value": "Data breach / theft",
  "w": 2,
  "pats": [
   "\\bdata breach\\b",
   "credentials (?:were )?(?:leaked|stolen)"
  ]
 },
 {
  "dim": "method",
  "value": "Physical theft",
  "w": 3,
  "pats": [
   "\\bstolen (?:wallet|card|phone)\\b",
   "\\bpickpocket"
  ]
 },
 {
  "dim": "method",
  "value": "In person contact",
  "w": 2,
  "pats": [
   "\\bin person\\b",
   "\\bat the branch\\b",
   "\\bdoorstep\\b"
  ]
 },
 {
  "dim": "modus",
  "value": "Safe account fraud",
  "w": 6,
  "pats": [
   "safe account",
   "secure account",
   "move (?:the |your )?(?:funds|money) to"
  ]
 },
 {
  "dim": "modus",
  "value": "Stop unauthorised transaction fraud",
  "w": 4,
  "pats": [
   "stop (?:an? )?unauthorised (?:transaction|payment)",
   "cancel (?:a |the )?fraudulent payment"
  ]
 },
 {
  "dim": "modus",
  "value": "Investment fraud",
  "w": 4,
  "pats": [
   "\\binvest(?:ment|ing)?\\b",
   "\\bcrypto\\b",
   "\\btrading (?:platform|account)\\b",
   "\\bportfolio\\b"
  ]
 },
 {
  "dim": "modus",
  "value": "Romance fraud",
  "w": 4,
  "pats": [
   "\\bromance\\b",
   "person they (?:met|had met) online",
   "\\bpartner they never met\\b"
  ]
 },
 {
  "dim": "modus",
  "value": "Support a friend or family member fraud",
  "w": 4,
  "pats": [
   "(?:son|daughter|child|mother|father|friend) (?:in trouble|needed|messaged)",
   "hi mum",
   "hi dad"
  ]
 },
 {
  "dim": "modus",
  "value": "Charity / donation fraud",
  "w": 4,
  "pats": [
   "\\bcharity\\b",
   "\\bdonation\\b"
  ]
 },
 {
  "dim": "modus",
  "value": "Online shopping fraud",
  "w": 4,
  "pats": [
   "\\bpurchase\\b",
   "\\bbought\\b",
   "\\bgoods\\b"
  ]
 },
 {
  "dim": "modus",
  "value": "Advance fee fraud",
  "w": 4,
  "pats": [
   "advance fee",
   "\\bupfront (?:fee|payment)\\b",
   "release the (?:funds|prize|inheritance)"
  ]
 },
 {
  "dim": "modus",
  "value": "Claim a benefit fraud",
  "w": 4,
  "pats": [
   "\\btax (?:refund|rebate)\\b",
   "\\bbenefit claim\\b",
   "government (?:grant|payment)"
  ]
 },
 {
  "dim": "modus",
  "value": "Extortion",
  "w": 4,
  "pats": [
   "\\bblackmail\\b",
   "\\bextort",
   "\\bransom\\b"
  ]
 },
 {
  "dim": "modus",
  "value": "Impersonation of creditor",
  "w": 4,
  "pats": [
   "changed (?:their |our )?(?:bank )?(?:account )?details",
   "new account number",
   "supplier (?:email|invoice)"
  ]
 },
 {
  "dim": "modus",
  "value": "Impersonation of person with authority to instruct payments",
  "w": 4,
  "pats": [
   "\\bceo\\b",
   "\\bchief executive\\b",
   "\\bpolice\\b",
   "\\btax authority\\b",
   "posing as (?:the |our )?(?:ceo|director)"
  ]
 },
 {
  "dim": "modus",
  "value": "Phoney debt/bill collection",
  "w": 4,
  "pats": [
   "\\boutstanding (?:debt|bill)\\b",
   "\\bdebt collect",
   "\\bunpaid invoice\\b"
  ]
 },
 {
  "dim": "modus",
  "value": "Fake institution",
  "w": 4,
  "pats": [
   "fake (?:bank|institution) (?:website|portal)",
   "log(?:ged)? in (?:to|on) a (?:fake|cloned)"
  ]
 },
 {
  "dim": "modus",
  "value": "Pure account takeover",
  "w": 3,
  "pats": [
   "account takeover",
   "took over the account",
   "logged in as the customer",
   "password was reset",
   "changed the (?:password|security details)"
  ]
 },
 {
  "dim": "modus",
  "value": "Pure account takeover",
  "w": 2,
  "pats": [
   "new device (?:was )?registered",
   "phone number (?:was )?changed",
   "\\bdormant\\b[^.]{0,60}reactivat"
  ]
 },
 {
  "dim": "modus",
  "value": "Control of card or card details by unauthorised party",
  "w": 4,
  "pats": [
   "card details? (?:were )?used",
   "card not present",
   "\\bcnp\\b"
  ]
 },
 {
  "dim": "modus",
  "value": "Creditor account data manipulation",
  "w": 3,
  "pats": [
   "beneficiary details (?:were )?changed",
   "payee (?:was )?(?:changed|swapped)"
  ]
 },
 {
  "dim": "modus",
  "value": "Fraudulent card application",
  "w": 4,
  "pats": [
   "card application",
   "applied for a card"
  ]
 },
 {
  "dim": "modus",
  "value": "Fraudulent card claim",
  "w": 4,
  "pats": [
   "chargeback claim",
   "false(?:ly)? claim"
  ]
 },
 {
  "dim": "modus",
  "value": "Fraudulent use of cash back scheme",
  "w": 4,
  "pats": [
   "cash ?back scheme"
  ]
 },
 {
  "dim": "initiator",
  "value": "Customer",
  "w": 3,
  "pats": [
   "customer (?:was )?(?:persuaded|instructed|told|convinced|manipulated)",
   "authorised (?:each|the) payments?",
   "approve[ds]? (?:two |the |both )?(?:prompts?|payments?)",
   "under instruction"
  ]
 },
 {
  "dim": "initiator",
  "value": "Customer",
  "w": 3,
  "pats": [
   "customer'?s own credentials",
   "approved in the (?:customer'?s )?(?:banking )?app"
  ]
 },
 {
  "dim": "initiator",
  "value": "Fraudster",
  "w": 2,
  "pats": [
   "new device (?:was )?registered",
   "phone number (?:was )?changed",
   "credentials (?:were )?reset"
  ]
 },
 {
  "dim": "initiator",
  "value": "Fraudster",
  "w": 3,
  "pats": [
   "without the customer",
   "did not authorise",
   "unauthorised (?:payment|transaction|access)",
   "took over the account"
  ]
 },
 {
  "dim": "initiator",
  "value": "First party",
  "w": 3,
  "pats": [
   "first party",
   "customer (?:themselves )?(?:fabricated|falsely claimed)"
  ]
 },
 {
  "dim": "instrument",
  "value": "Account-to-account transaction",
  "w": 2,
  "pats": [
   "\\btransfer(?:red|s)?\\b",
   "\\bpayment to\\b",
   "\\[IBAN\\]",
   "\\bcredit transfer\\b"
  ]
 },
 {
  "dim": "instrument",
  "value": "Card payment",
  "w": 2,
  "pats": [
   "\\bcard payment\\b",
   "\\[CARD\\]",
   "\\bon (?:their|the) card\\b"
  ]
 },
 {
  "dim": "labels",
  "value": "Money muling",
  "w": 3,
  "pats": [
   "\\bmule\\b",
   "receiving account",
   "funds (?:were )?(?:moved|forwarded) on"
  ]
 },
 {
  "dim": "labels",
  "value": "Card chip relay",
  "w": 3,
  "pats": [
   "chip relay",
   "relay attack"
  ]
 },
 {
  "dim": "labels",
  "value": "Smishing",
  "w": 3,
  "pats": [
   "text message[^.]{0,80}(?:link|cloned)",
   "\\bsmishing\\b"
  ]
 },
 {
  "dim": "labels",
  "value": "Vishing",
  "w": 3,
  "pats": [
   "(?:call|phone)[^.]{0,60}(?:claiming to be|from the bank|security team)",
   "claiming to be from[^.]{0,40}(?:bank|security)",
   "\\bvishing\\b"
  ]
 },
 {
  "dim": "labels",
  "value": "Phishing",
  "w": 3,
  "pats": [
   "cloned (?:version|login|site|website)",
   "\\bphishing\\b"
  ]
 },
 {
  "dim": "labels",
  "value": "Fake bank / financial institution",
  "w": 2,
  "pats": [
   "claiming to be (?:from )?(?:the |our )?bank",
   "posing as the bank"
  ]
 }
];
