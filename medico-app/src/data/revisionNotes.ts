export interface RevisionSection {
  title: string;
  points: string[];
}

export interface SubjectRevision {
  subject: string;
  color: string; // Tailwind bg class
  sections: RevisionSection[];
}

export const REVISION_NOTES: SubjectRevision[] = [
  {
    subject: 'Anatomy',
    color: 'bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300',
    sections: [
      {
        title: 'Rotator Cuff & Shoulder',
        points: [
          'SITS: Supraspinatus (abduction 0–15°), Infraspinatus, Teres minor (lateral rotation), Subscapularis (medial rotation)',
          'Most common rotator cuff tear: Supraspinatus',
          'Quadrangular space: axillary nerve + posterior circumflex humeral artery',
          'Triangular space: circumflex scapular artery',
          'Triangular interval: radial nerve + profunda brachii',
        ],
      },
      {
        title: 'Nerve Injuries',
        points: [
          'Wrist drop: radial nerve (spiral groove of humerus)',
          'Claw hand: ulnar nerve (medial epicondyle)',
          'Ape thumb / pen-holding deformity: median nerve (carpal tunnel)',
          'Foot drop: common peroneal nerve (neck of fibula)',
          'Meralgia paraesthetica: lateral femoral cutaneous nerve',
          'Long thoracic nerve injury → winged scapula',
          'Axillary nerve injury → loss of shoulder abduction (deltoid)',
        ],
      },
      {
        title: 'Important Foramina & Spaces',
        points: [
          'Foramen spinosum: middle meningeal artery',
          'Foramen ovale: mandibular nerve (V3)',
          'Jugular foramen: IX, X, XI + sigmoid sinus → internal jugular vein',
          'Carpal tunnel contents: 4 FDS, 4 FDP, FPL (9 tendons) + median nerve',
          'Femoral canal: lymphatics + areolar tissue (medial to femoral vein)',
        ],
      },
      {
        title: 'Lymphatic Drainage',
        points: [
          'Testes → para-aortic nodes (NOT inguinal)',
          'Scrotum → superficial inguinal nodes',
          'Anal canal above pectinate line → internal iliac nodes',
          'Anal canal below pectinate line → superficial inguinal nodes',
          'Lower limb, perineum, scrotum, vagina below introitus → inguinal nodes',
        ],
      },
    ],
  },
  {
    subject: 'Physiology',
    color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    sections: [
      {
        title: 'Normal Values (Memorise)',
        points: [
          'GFR: 125 mL/min; RBF: 1200 mL/min; RPF: 600 mL/min',
          'Filtration fraction = GFR/RPF = 125/600 ≈ 0.2 (20%)',
          'Cardiac output: 5 L/min; Stroke volume: 70 mL; HR: 72 bpm',
          'PaO₂: 95 mmHg; PaCO₂: 40 mmHg; pH: 7.4; HCO₃⁻: 24 mEq/L',
          'RBC life span: 120 days; Platelet: 7–10 days; WBC: hours–days',
          'Normal IOP: 10–21 mmHg; CSF pressure: 70–180 mmH₂O',
        ],
      },
      {
        title: 'Action Potential & Nerve',
        points: [
          'Resting membrane potential: −70 mV (neurons), −90 mV (cardiac muscle)',
          'Threshold: −55 mV; Overshoot: +30 mV',
          'Fastest conduction: A-alpha fibres (motor, proprioception)',
          'Slowest conduction: C fibres (unmyelinated, pain, autonomic)',
          'Absolute refractory period: no stimulus can trigger AP (Na⁺ channels inactivated)',
          'Relative refractory period: suprathreshold stimulus needed',
        ],
      },
      {
        title: 'Respiratory',
        points: [
          'TV: 500 mL; IRV: 3000 mL; ERV: 1100 mL; RV: 1200 mL',
          'VC = IRV + TV + ERV = 4600 mL',
          'FRC = ERV + RV = 2300 mL (cannot be measured by spirometry)',
          'Hering-Breuer reflex: lung stretch → inhibits inspiration',
          'Hypoxic pulmonary vasoconstriction (HPV): unique to lung — diverts blood from poorly ventilated areas',
          'CO₂ is primary drive; hypoxia is drive in COPD (peripheral chemoreceptors)',
        ],
      },
      {
        title: 'Renal & Hormones',
        points: [
          'ADH (vasopressin): acts on collecting duct (V2 receptors) → inserts AQP2',
          'Aldosterone: acts on DCT/collecting duct → Na⁺ reabsorption, K⁺ & H⁺ excretion',
          'ANP: released from atria in response to stretch → natriuresis, vasodilation',
          'PTH: increases serum Ca²⁺ (bones, kidney) → decreases phosphate',
          'Calcitonin: decreases serum Ca²⁺ (released from parafollicular C cells)',
          'Insulin: only hormone that lowers blood glucose; promotes glycogen synthesis',
        ],
      },
    ],
  },
  {
    subject: 'Biochemistry',
    color: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-300',
    sections: [
      {
        title: 'Vitamins (Key Facts)',
        points: [
          'B1 (Thiamine): Beriberi, Wernicke–Korsakoff; cofactor for pyruvate dehydrogenase',
          'B2 (Riboflavin): Ariboflavinosis, corneal vascularization; FAD/FMN',
          'B3 (Niacin): Pellagra (3 Ds: Dermatitis, Diarrhoea, Dementia); Hartnup disease',
          'B6 (Pyridoxine): Sideroblastic anaemia, peripheral neuropathy (INH side effect)',
          'B9 (Folic acid): NTDs; megaloblastic anaemia; no neurological symptoms',
          'B12 (Cobalamin): Megaloblastic anaemia + subacute combined degeneration of cord',
          'Vit C: Scurvy (perifollicular haemorrhage, corkscrew hairs); cofactor for collagen hydroxylation',
          'Vit D: Rickets (children), Osteomalacia (adults); activated by 1α-hydroxylase (kidney)',
          'Vit K: Clotting factors II, VII, IX, X; deficiency → increased PT',
        ],
      },
      {
        title: 'Key Enzymes & Pathways',
        points: [
          'Rate-limiting enzyme of glycolysis: Phosphofructokinase-1 (PFK-1)',
          'Rate-limiting in TCA: Isocitrate dehydrogenase',
          'Rate-limiting in gluconeogenesis: Fructose-1,6-bisphosphatase',
          'Rate-limiting in cholesterol synthesis: HMG-CoA reductase (target of statins)',
          'Rate-limiting in urea cycle: Carbamoyl phosphate synthetase I',
          'Pyruvate dehydrogenase complex: requires B1, B2, B3, B5, lipoic acid',
          'Glycogen storage: Liver — glucose-6-phosphatase (absent in muscle); Muscle — myophosphorylase',
        ],
      },
      {
        title: 'Metabolism Disorders',
        points: [
          'PKU: Phenylalanine hydroxylase deficiency → musty odour, fair skin, intellectual disability',
          'Maple syrup urine disease: BCAA decarboxylase deficiency (Leu, Ile, Val)',
          'Homocystinuria: Cystathionine β-synthase deficiency → lens dislocation (down & in)',
          'Alkaptonuria: Homogentisate oxidase deficiency → ochronosis, dark urine',
          'Gaucher: β-glucocerebrosidase deficiency → Gaucher cells (crumpled paper)',
          'Niemann-Pick: Sphingomyelinase deficiency → foam cells',
          'Tay-Sachs: Hexosaminidase A deficiency → cherry red spot, no organomegaly',
        ],
      },
      {
        title: 'DNA & Molecular Biology',
        points: [
          'DNA replication is semi-conservative (Meselson-Stahl experiment)',
          'Primase synthesizes RNA primer; DNA Pol III elongates; DNA Pol I removes primer',
          'Transition: purine↔purine or pyrimidine↔pyrimidine; Transversion: purine↔pyrimidine',
          'p53: guardian of genome; mutated in 50% of cancers',
          'Oncogenes: gain-of-function (dominant); Tumour suppressors: loss-of-function (recessive)',
          'Ras oncogene: most common in human cancers; GTPase activity lost',
        ],
      },
    ],
  },
  {
    subject: 'Pharmacology',
    color: 'bg-pink-100 text-pink-700 dark:bg-pink-900/40 dark:text-pink-300',
    sections: [
      {
        title: 'Drugs of Choice',
        points: [
          'Drug of choice (DOC) for malaria: Chloroquine (sensitive P. falciparum); Artemisinin (resistant)',
          'DOC for typhoid: Ceftriaxone (or Azithromycin); Fluoroquinolones in uncomplicated',
          'DOC for TB: HRZE (Isoniazid, Rifampicin, Pyrazinamide, Ethambutol) × 2 months, then HR × 4 months',
          'DOC for leprosy MB: Rifampicin + Dapsone + Clofazimine × 12 months',
          'DOC for status epilepticus: Lorazepam (IV); then Phenytoin/Valproate',
          'DOC for tonic-clonic seizures: Valproate (both partial and generalized)',
          'DOC for absence seizures: Ethosuximide (or Valproate)',
          'DOC for trigeminal neuralgia: Carbamazepine',
        ],
      },
      {
        title: 'Important Side Effects',
        points: [
          'Chloroquine: Retinopathy (bull\'s eye maculopathy)',
          'Isoniazid: Peripheral neuropathy (B6 deficiency), hepatitis, lupus',
          'Rifampicin: Orange discolouration of body fluids, hepatitis, enzyme inducer',
          'Ethambutol: Optic neuritis (colour vision lost first)',
          'Pyrazinamide: Hyperuricaemia (gout)',
          'Amiodarone: Thyroid dysfunction, pulmonary fibrosis, corneal microdeposits, photosensitivity',
          'Metformin: Lactic acidosis (contraindicated in renal failure), no hypoglycaemia',
          'Clozapine: Agranulocytosis (requires CBC monitoring)',
        ],
      },
      {
        title: 'Receptor Pharmacology',
        points: [
          'β1: Heart (inotropy, chronotropy); β2: Lungs, vessels (bronchodilation, vasodilation)',
          'α1: Vasoconstriction; α2: Presynaptic (inhibits NE release)',
          'M1: CNS, ganglia; M2: Heart (slows HR); M3: Smooth muscle, glands',
          'Atropine blocks all muscarinic receptors (competitive antagonist)',
          'Selective β1 blockers: Metoprolol, Atenolol, Bisoprolol (safe in asthmatics)',
          'Non-selective β blockers: Propranolol (also has quinidine-like effect)',
        ],
      },
      {
        title: 'Pharmacokinetics',
        points: [
          'Zero-order kinetics: constant amount eliminated regardless of concentration (Alcohol, Phenytoin, Aspirin at high doses)',
          'First-order kinetics: constant fraction eliminated (most drugs)',
          'Half-life = 0.693 × Vd / CL',
          'Steady state reached in ~5 half-lives',
          'Bioavailability: IV = 100%; oral varies with first-pass metabolism',
          'Drugs with high first-pass: Propranolol, Lignocaine, Morphine, GTN',
        ],
      },
    ],
  },
  {
    subject: 'Pathology',
    color: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
    sections: [
      {
        title: 'Cell Injury & Death',
        points: [
          'Reversible injury: cellular swelling, fatty change',
          'Irreversible injury: nuclear changes — pyknosis → karyorrhexis → karyolysis',
          'Apoptosis: programmed, energy-dependent, no inflammation; Necrosis: pathological, inflammation',
          'Coagulative necrosis: most common; preserved cell outline; heart, kidney (except renal papillae)',
          'Liquefactive necrosis: brain infarct, abscess; cell outline lost',
          'Caseous necrosis: cheese-like, TB characteristic',
          'Fibrinoid necrosis: immune complexes, vasculitis, malignant hypertension',
        ],
      },
      {
        title: 'Tumour Markers',
        points: [
          'AFP: Hepatocellular carcinoma, Yolk sac tumour, NTD screening',
          'CEA: Colorectal carcinoma (non-specific); also lung, breast, gastric',
          'PSA: Prostate carcinoma (most specific)',
          'CA 125: Ovarian carcinoma (serous cystadenocarcinoma)',
          'CA 19-9: Pancreatic carcinoma',
          'β-hCG: Choriocarcinoma, gestational trophoblastic disease',
          'LDH: Non-specific; useful in NHL, seminoma',
          'Calcitonin: Medullary thyroid carcinoma',
        ],
      },
      {
        title: 'Genetics of Cancer',
        points: [
          'Li-Fraumeni syndrome: p53 mutation → multiple cancers',
          'BRCA1/2: Breast, ovarian cancer',
          'APC gene: Familial adenomatous polyposis → colorectal cancer',
          'VHL gene: Renal cell carcinoma, haemangioblastoma',
          'RB1 gene: Retinoblastoma (two-hit hypothesis)',
          'BCR-ABL t(9;22) Philadelphia chromosome: CML (imatinib target)',
          't(14;18): Follicular lymphoma (BCL-2 overexpression)',
          't(8;14): Burkitt lymphoma (c-MYC)',
        ],
      },
      {
        title: 'Amyloidosis & Inflamm.',
        points: [
          'AL amyloid: Plasma cell dyscrasias (myeloma) — systemic',
          'AA amyloid: Chronic inflammation (TB, RA, bronchiectasis)',
          'Aβ amyloid: Alzheimer disease (senile plaques)',
          'Granuloma: Epithelioid cells + Langhans giant cells',
          'TB granuloma: caseation centre + Langhans cells',
          'Sarcoidosis: non-caseating granuloma + asteroid bodies + Schaumann bodies',
          'Acute inflammation mediators: Histamine (immediate), PG/LT (sustained), PAF, IL-1, TNF-α',
        ],
      },
    ],
  },
  {
    subject: 'Microbiology',
    color: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    sections: [
      {
        title: 'Staining & Culture',
        points: [
          'Gram positive: thick peptidoglycan — retains crystal violet (purple)',
          'Gram negative: thin PG + outer membrane — safranin (pink/red)',
          'Acid-fast (ZN stain): Mycobacterium, Nocardia',
          'India ink: Cryptococcus neoformans (capsule)',
          'PAS stain: Fungi, Whipple\'s disease (T. whipplei)',
          'Silver stain: Pneumocystis jirovecii, Histoplasma, Legionella',
          'Loeffler\'s serum slope: Corynebacterium diphtheriae',
          'Charcoal-yeast extract (BCYE): Legionella pneumophila',
        ],
      },
      {
        title: 'Virulence Factors',
        points: [
          'Protein A: S. aureus → binds Fc of IgG (anti-opsonin)',
          'Protein M: S. pyogenes → anti-phagocytic',
          'IgA protease: N. gonorrhoeae, N. meningitidis, H. influenzae, S. pneumoniae',
          'Exotoxin A: P. aeruginosa (ADP-ribosylation of EF-2, like diphtheria toxin)',
          'TSST-1: S. aureus superantigen → toxic shock syndrome',
          'Streptolysin O (SLO): S. pyogenes — immunogenic (ASO titre)',
          'Coagulase: S. aureus only (distinguishes from coagulase-negative staph)',
        ],
      },
      {
        title: 'Important Organisms',
        points: [
          'Most common cause of meningitis: Neisseria meningitidis (young adults); S. pneumoniae (elderly)',
          'Neonatal meningitis: Group B Streptococcus, E. coli, Listeria',
          'Waterhouse-Friderichsen syndrome: N. meningitidis → bilateral adrenal haemorrhage',
          'Ghon\'s focus: Primary TB complex (Ghon focus + enlarged lymph node = Ghon\'s complex)',
          'Most common cause of UTI: E. coli (80%), then Klebsiella, S. saprophyticus (young women)',
          'Pseudomembranous colitis: C. difficile (toxin A + B) → after antibiotic use',
        ],
      },
      {
        title: 'Hepatitis Serology',
        points: [
          'HBsAg: Surface antigen — first marker of active infection',
          'Anti-HBs: Recovery/immunity (vaccination)',
          'HBeAg: High infectivity',
          'Anti-HBc IgM: Acute infection (window period marker)',
          'Anti-HBc IgG: Past exposure',
          'Window period: HBsAg gone, Anti-HBs not yet present → only Anti-HBc IgM positive',
          'HDV: requires HBsAg for replication; coinfection vs superinfection',
          'HCV: RNA virus, flavivirus; chronic infection in 85%; leading cause of liver transplant',
        ],
      },
    ],
  },
  {
    subject: 'Medicine',
    color: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    sections: [
      {
        title: 'Cardiovascular',
        points: [
          'MI: STEMI → thrombolysis/PCI; NSTEMI → anticoagulation + PCI',
          'Heart failure: EF <40% = HFrEF (systolic); EF ≥50% = HFpEF (diastolic)',
          'First-line HF: ACEI/ARB + β-blocker + spironolactone + SGLT2i',
          'Cardiac tamponade: Beck\'s triad — hypotension, JVD, muffled heart sounds',
          'Aortic stenosis: ejection systolic murmur + slow rising pulse + narrow pulse pressure',
          'Mitral regurgitation: holosystolic murmur at apex radiating to axilla',
          'AF: Rate control (β-blocker/diltiazem) vs rhythm control; anticoagulate if CHA₂DS₂-VASc ≥1 (men) /2 (women)',
        ],
      },
      {
        title: 'Endocrinology',
        points: [
          'DM diagnosis: FBS ≥126 mg/dL, 2hr OGTT ≥200, HbA1c ≥6.5%, random ≥200 + symptoms',
          'HbA1c: reflects average glucose over 3 months',
          'DKA: Type 1 DM; anion gap acidosis; treat with IV fluids + insulin + K⁺ replacement',
          'Cushing\'s: High cortisol; buffalo hump, moon face, striae, hypertension',
          'Addison\'s: Low cortisol; hyperpigmentation, hypotension, hyponatraemia, hyperkalaemia',
          'Hypothyroidism: High TSH, low T4; bradycardia, weight gain, constipation',
          'Primary hyperaldosteronism (Conn\'s): hypertension + hypokalaemia + low renin',
        ],
      },
      {
        title: 'Rheumatology',
        points: [
          'RA: Symmetrical small joint arthritis; RF+, anti-CCP+; morning stiffness >1 hour',
          'SLE: butterfly rash, photosensitivity, ANA+ (95%), anti-dsDNA (specific), anti-Sm (specific)',
          'Scleroderma: anti-Scl-70 (diffuse), anti-centromere (limited/CREST)',
          'Sjögren\'s: anti-Ro (SS-A), anti-La (SS-B); dry eyes + dry mouth',
          'Ankylosing spondylitis: HLA-B27, sacroiliitis, bamboo spine',
          'Reactive arthritis: urethritis + conjunctivitis + arthritis (can\'t see, can\'t pee, can\'t climb a tree)',
          'Gout: urate crystals (negatively birefringent, needle-shaped); DOC acute: NSAIDs/colchicine',
        ],
      },
      {
        title: 'Acid-Base',
        points: [
          'Metabolic acidosis: low pH, low HCO₃⁻; causes: DKA, lactic acidosis, renal failure, diarrhoea',
          'Metabolic alkalosis: high pH, high HCO₃⁻; causes: vomiting, diuretics, Cushing\'s',
          'Respiratory acidosis: low pH, high PaCO₂; COPD, hypoventilation',
          'Respiratory alkalosis: high pH, low PaCO₂; anxiety, PE, high altitude',
          'Anion gap = Na⁺ − (Cl⁻ + HCO₃⁻); normal = 8–12; elevated in MUDPILES',
          'MUDPILES: Methanol, Uraemia, DKA, Paraldehyde, INH, Lactic acidosis, Ethylene glycol, Salicylates',
        ],
      },
    ],
  },
  {
    subject: 'Surgery',
    color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
    sections: [
      {
        title: 'Hernias',
        points: [
          'Indirect inguinal: through deep inguinal ring; lateral to inferior epigastric vessels',
          'Direct inguinal: through Hesselbach\'s triangle; medial to inferior epigastric vessels',
          'Femoral hernia: through femoral ring; most common in women; high risk of strangulation',
          'Richter\'s hernia: part of bowel wall trapped (antimesenteric border) — no obstruction',
          'Littre\'s hernia: contains Meckel\'s diverticulum',
          'Maydl\'s hernia (W hernia): two loops in sac with intervening loop inside abdomen',
        ],
      },
      {
        title: 'Thyroid & Neck',
        points: [
          'Papillary thyroid cancer: most common (80%); psammoma bodies; lymph node spread',
          'Follicular thyroid cancer: haematogenous spread; cold nodule; vascular invasion',
          'Medullary thyroid cancer: C cells (calcitonin); MEN 2A and 2B',
          'Anaplastic: worst prognosis; rapidly growing, elderly',
          'Thyroglossal cyst: moves with swallowing AND protrusion of tongue',
          'Branchial cyst: from 2nd branchial arch; anterior triangle, deep to SCM',
        ],
      },
      {
        title: 'Colorectal',
        points: [
          'Duke\'s staging: A (mucosa/submucosa), B (muscle), C (lymph nodes), D (distant mets)',
          'Most common site for colorectal cancer: rectosigmoid junction',
          'CEA: not for diagnosis, used for monitoring recurrence post-op',
          'FAP: APC gene mutation, 100% lifetime risk of colorectal cancer',
          'HNPCC (Lynch): mismatch repair genes (MLH1, MSH2); proximal colon',
          'Intussusception: most common in children 6 months–2 years; ileocolic; redcurrant jelly stools',
        ],
      },
      {
        title: 'Trauma & Fluids',
        points: [
          'Parkland formula: 4 × weight(kg) × %TBSA burns; give half in first 8 hours',
          'Hartmann\'s solution = Ringer\'s lactate (most physiological crystalloid)',
          'Class I haemorrhage: <750 mL (<15%); no change in vitals',
          'Class II: 750–1500 mL; tachycardia, anxiety',
          'Class III: 1500–2000 mL; hypotension, confusion',
          'Class IV: >2000 mL; life-threatening; immediate surgery',
        ],
      },
    ],
  },
  {
    subject: 'Obstetrics & Gynaecology',
    color: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
    sections: [
      {
        title: 'Obstetrics Key Points',
        points: [
          'Nagele\'s rule: EDD = LMP + 9 months + 7 days',
          'Pre-eclampsia: BP ≥140/90 + proteinuria after 20 weeks; treat with labetalol/methyldopa/nifedipine',
          'Eclampsia: seizures in pre-eclampsia; MgSO₄ is DOC for prevention and treatment',
          'Placenta praevia: painless bleeding; placenta covers internal os; C-section if type III/IV',
          'Placental abruption: painful bleeding; concealed or revealed; board-like uterus',
          'Cord prolapse: emergency; knee-chest position + emergency C-section',
          'Bishop score ≥8 → favourable cervix for induction',
        ],
      },
      {
        title: 'Gynaecology',
        points: [
          'Most common gynaecological malignancy: Endometrial carcinoma (postmenopausal bleeding)',
          'Most common ovarian malignancy: Serous cystadenocarcinoma (CA-125)',
          'PCOS: oligomenorrhoea, hyperandrogenism, polycystic ovaries (2 of 3 Rotterdam criteria)',
          'PCOS treatment: Metformin (insulin resistance), OCPs (cycle regulation), Clomiphene (ovulation induction)',
          'Endometriosis: chocolate cysts (endometrioma) on ovaries; CA-125 elevated; chocolate cyst',
          'Fibroid: most common benign tumour in women; oestrogen-dependent; whorled pattern',
        ],
      },
      {
        title: 'Cervical Cancer',
        points: [
          'HPV 16 & 18: high-risk strains; cause 70% of cervical cancers',
          'HPV 6 & 11: low-risk; condyloma acuminata (genital warts)',
          'Pap smear screening: 21–65 years every 3 years (or 5-yearly with HPV co-test)',
          'CIN grading: CIN I (mild), CIN II (moderate), CIN III (severe/CIS)',
          'Colposcopy: for abnormal Pap smear; aceto-white areas, mosaic pattern',
          'Stage IB+ cervical cancer → radical hysterectomy + lymph node dissection',
        ],
      },
    ],
  },
  {
    subject: 'Paediatrics',
    color: 'bg-lime-100 text-lime-700 dark:bg-lime-900/40 dark:text-lime-300',
    sections: [
      {
        title: 'Developmental Milestones',
        points: [
          '3 months: social smile, holds head up in prone',
          '6 months: sits with support, transfers objects, babbles',
          '9 months: sits without support, pincer grasp developing, stranger anxiety',
          '12 months: walks with support, first words (mama/papa with meaning), pincer grasp complete',
          '18 months: walks independently, 10 words, uses spoon',
          '2 years: runs, 2–3 word sentences, 50 words',
          '3 years: climbs stairs alternating feet, 3-word sentences, knows name/age/sex',
        ],
      },
      {
        title: 'Paediatric Emergencies',
        points: [
          'Febrile seizures: 6 months–5 years; simple (<15 min, generalised, once in 24h) vs complex',
          'Croup (laryngotracheobronchitis): parainfluenza; steeple sign on X-ray; nebulised adrenaline',
          'Epiglottitis: H. influenzae type b; thumbprint sign; do NOT examine throat; emergency',
          'Intussusception: redcurrant jelly stools; dance sign (empty RIF); air enema reduction',
          'Kawasaki disease: fever >5 days + 4/5 criteria (rash, conjunctivitis, lymphadenopathy, strawberry tongue, hand/foot changes)',
          'Kawasaki DOC: IV Ig + aspirin',
        ],
      },
      {
        title: 'Neonatology',
        points: [
          'APGAR score: Appearance, Pulse, Grimace, Activity, Respiration; scored 0–2 each; >7 = normal',
          'Respiratory distress syndrome (RDS): surfactant deficiency; premature; ground glass on CXR',
          'Treatment of RDS: exogenous surfactant + CPAP/ventilation; antenatal steroids for prevention',
          'Physiological jaundice: appears day 2–3, resolves by day 14 (phototherapy if high)',
          'Pathological jaundice: appears <24 hours → haemolytic (Rh/ABO incompatibility)',
          'Erythroblastosis fetalis: Rh incompatibility; prevent with anti-D immunoglobulin at 28 weeks + delivery',
        ],
      },
    ],
  },
  {
    subject: 'Psychiatry',
    color: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300',
    sections: [
      {
        title: 'Schizophrenia & Psychosis',
        points: [
          'Positive symptoms: hallucinations (auditory > visual), delusions, disorganised speech',
          'Negative symptoms: flat affect, alogia, avolition, anhedonia, social withdrawal',
          'First-line: atypical antipsychotics (olanzapine, risperidone, aripiprazole)',
          'Clozapine: treatment-resistant schizophrenia; requires WBC monitoring (agranulocytosis)',
          'NMS (Neuroleptic Malignant Syndrome): hyperthermia, rigidity, autonomic instability, altered consciousness',
          'NMS treatment: stop antipsychotic; dantrolene + bromocriptine',
          'Tardive dyskinesia: late-onset repetitive involuntary movements; from long-term antipsychotics',
        ],
      },
      {
        title: 'Mood Disorders',
        points: [
          'Major Depression: SIGECAPS (Sleep, Interest, Guilt, Energy, Concentration, Appetite, Psychomotor, Suicidal thoughts) × 2 weeks',
          'First-line treatment: SSRIs (fluoxetine, sertraline)',
          'TCA side effects: anticholinergic, cardiac arrhythmias, sedation; dangerous in overdose',
          'Bipolar I: manic episode (≥7 days) ± depression; Bipolar II: hypomania + depression',
          'Lithium: for bipolar; narrow therapeutic index; monitor thyroid, renal, serum levels',
          'Lithium toxicity: coarse tremor, confusion, polyuria/polydipsia; treat with NS infusion',
        ],
      },
      {
        title: 'Anxiety & Others',
        points: [
          'GAD: excessive anxiety ≥6 months; DOC: SSRI/SNRI + buspirone/benzos short-term',
          'Panic disorder: recurrent unexpected attacks; agoraphobia common; SSRIs + CBT',
          'OCD: ego-dystonic obsessions + compulsions; SSRIs (high dose) + CBT',
          'PTSD: re-experiencing, avoidance, hyperarousal after trauma; SSRIs + trauma-focused CBT',
          'Alzheimer\'s: most common dementia; ACh deficiency; donepezil, rivastigmine',
          'Delirium: acute onset, fluctuating, reversible; treat underlying cause',
        ],
      },
    ],
  },
  {
    subject: 'Forensic Medicine',
    color: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800/60 dark:text-zinc-300',
    sections: [
      {
        title: 'Post-mortem Changes',
        points: [
          'Cooling (algor mortis): body cools at ~1°C/hour after death',
          'Rigor mortis: starts 2–6 hours, complete 12 hours, disappears 24–48 hours; starts in small muscles',
          'Livor mortis (hypostasis): 1–2 hours after death; fixed at 6–8 hours',
          'Decomposition sequence: fresh → bloat → active decay → advanced decay → dry remains',
          'Cadaveric spasm: instantaneous rigor at moment of death; persists (indicates ante-mortem)',
        ],
      },
      {
        title: 'Wounds & Injuries',
        points: [
          'Incised wound: sharp weapon, edges sharp, length > depth',
          'Lacerated wound: blunt force, irregular margins, depth > length',
          'Contusion (bruise): extravasation of blood; age estimation by colour',
          'Contact gunshot: muzzle contusion, blackening, tattooing, bullet hole',
          'Entrance wound (close range): small, regular, inverted edges',
          'Exit wound: larger, irregular, everted edges (no blackening)',
          'Hesitation cuts: multiple superficial incised wounds on wrist/neck in suicides',
        ],
      },
      {
        title: 'Toxicology',
        points: [
          'Organophosphate poisoning: SLUDGE (Salivation, Lacrimation, Urination, Defecation, GI distress, Emesis) + bradycardia, miosis',
          'OP treatment: Atropine (antidote) + pralidoxime (2-PAM, within 24h)',
          'CO poisoning: carboxyhaemoglobin; cherry red skin; treat with 100% O₂',
          'Cyanide poisoning: smells of bitter almonds; histotoxic hypoxia; treat with Na nitrite + Na thiosulfate',
          'Arsenic poisoning: Mees\' lines (transverse white lines on nails), garlic odour',
          'Lead poisoning: basophilic stippling of RBCs, Burton\'s line (blue line on gums)',
        ],
      },
    ],
  },
  {
    subject: 'Community Medicine',
    color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
    sections: [
      {
        title: 'Epidemiology',
        points: [
          'Incidence: new cases in a period; Prevalence: all cases at a point in time',
          'Prevalence = Incidence × Duration',
          'Sensitivity: TP/(TP+FN) — ability to detect true positives (used for screening)',
          'Specificity: TN/(TN+FP) — ability to detect true negatives (used for confirmation)',
          'PPV increases with higher prevalence; NPV increases with lower prevalence',
          'Relative risk (RR): cohort studies; Odds ratio (OR): case-control studies',
          'NNT = 1/ARR (Absolute Risk Reduction)',
        ],
      },
      {
        title: 'National Health Programs',
        points: [
          'Universal Immunisation Programme (UIP): BCG, OPV, DPT, Hepatitis B, Measles/MR, JE, Rotavirus, PCV',
          'BCG at birth; Hepatitis B at birth, 6w, 10w, 14w; OPV at 6w, 10w, 14w',
          'MR vaccine at 9–12 months and 16–24 months',
          'ASHA: trained for 1000 population; village health worker',
          'Pulse Polio: zero-dose OPV campaign; aim to eradicate polio',
          'India declared polio-free: 27 March 2014',
        ],
      },
      {
        title: 'Nutrition & Indices',
        points: [
          'BMI: weight(kg)/height(m²); normal 18.5–24.9; obese ≥30',
          'Marasmus: calorie deficiency; wasting, wizened face, no oedema',
          'Kwashiorkor: protein deficiency; oedema, moon face, flaky paint dermatosis, flag sign',
          'MUAC <115 mm: severe acute malnutrition in children',
          'Recommended protein intake: 0.8 g/kg/day (adults); 1.2–2 g/kg/day (growing children)',
          'Iodine deficiency: goitre, cretinism; prevent with iodised salt (≥15 ppm iodine)',
        ],
      },
    ],
  },
  {
    subject: 'Ophthalmology',
    color: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300',
    sections: [
      {
        title: 'Glaucoma',
        points: [
          'Primary open-angle glaucoma: most common; painless progressive visual field loss; optic disc cupping',
          'Acute closed-angle glaucoma: painful red eye, halos, nausea; narrow angle → emergency',
          'Treatment: β-blockers (timolol), prostaglandin analogues (latanoprost), carbonic anhydrase inhibitors',
          'Acute attack treatment: IV acetazolamide + pilocarpine + laser iridotomy',
          'IOP: normal 10–21 mmHg; measured by Goldmann applanation tonometry',
        ],
      },
      {
        title: 'Cataracts & Retina',
        points: [
          'Most common cause of cataract worldwide: age-related (senile)',
          'Congenital cataract: TORCH infections, galactosaemia, Down syndrome',
          'Diabetic retinopathy: NPDR (microaneurysms, exudates, haemorrhages) → PDR (neovascularisation)',
          'Central retinal artery occlusion: sudden painless visual loss; cherry red spot at fovea',
          'Central retinal vein occlusion: "stormy sunset" fundus; disc oedema, flame haemorrhages',
          'Retinal detachment: flashes + floaters + "curtain" vision loss; emergency',
        ],
      },
    ],
  },
  {
    subject: 'ENT',
    color: 'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300',
    sections: [
      {
        title: 'Ear',
        points: [
          'CSOM: chronic discharge + conductive hearing loss; central perforation (safe) vs marginal/attic (unsafe = cholesteatoma)',
          'Cholesteatoma: keratinising squamous epithelium in middle ear; erodes bone; surgery required',
          'Otosclerosis: autosomal dominant; stapes fixation; conductive hearing loss; Carhart\'s notch on audiometry',
          'Menière\'s disease: fluctuating hearing loss, tinnitus, vertigo, aural fullness',
          'Acoustic neuroma (vestibular schwannoma): CN VIII; unilateral SNHL + tinnitus',
          'BPPV: most common cause of vertigo; posterior semicircular canal; Epley manoeuvre',
        ],
      },
      {
        title: 'Nose & Throat',
        points: [
          'Epistaxis: Little\'s area (Kiesselbach\'s plexus) — most common site, anterior inferior septum',
          'Allergic rhinitis: eosinophilia in nasal smear; Pale boggy turbinates',
          'Carcinoma nasopharynx: EBV; unilateral secretory otitis media in adult → suspect',
          'Tonsillitis: Group A β-haemolytic streptococcus most common; treat with penicillin',
          'Quinsy (peritonsillar abscess): displacement of uvula, muffled voice, trismus',
          'Laryngeal carcinoma: supraglottic (dysphagia first), glottic (hoarseness first, best prognosis)',
        ],
      },
    ],
  },
  {
    subject: 'Dermatology',
    color: 'bg-fuchsia-100 text-fuchsia-700 dark:bg-fuchsia-900/40 dark:text-fuchsia-300',
    sections: [
      {
        title: 'Skin Lesions & Infections',
        points: [
          'Psoriasis: well-defined silvery-white plaques on extensor surfaces; Auspitz sign, Koebner phenomenon',
          'Lichen planus: 6 Ps — Pruritic, Polygonal, Purple, Planar (flat-topped) Papules & Plaques; Wickham\'s striae',
          'Pemphigus vulgaris: acantholysis, Nikolsky sign positive, intraepidermal blister; high mortality',
          'Bullous pemphigoid: subepidermal blister, Nikolsky sign negative; elderly',
          'Dermatitis herpetiformis: gluten-sensitive; IgA deposits at dermal papillae; associated with coeliac disease',
          'Leprosy: TT (tuberculoid, cell-mediated, few bacilli) vs LL (lepromatous, humoral, many bacilli)',
        ],
      },
      {
        title: 'Skin Cancer',
        points: [
          'BCC (Basal cell carcinoma): most common skin cancer; pearly nodule, rolled edges; locally invasive, rarely metastasises',
          'SCC (Squamous cell carcinoma): second most common; sun-exposed areas; arises from actinic keratosis',
          'Melanoma: ABCDE criteria (Asymmetry, Border, Colour, Diameter >6mm, Evolution)',
          'Clark\'s levels: invasion depth (I=epidermis, V=subcutaneous fat)',
          'Breslow thickness: most important prognostic factor in melanoma',
          'Marjolin\'s ulcer: SCC arising in chronic ulcer/scar (e.g. burn scar)',
        ],
      },
    ],
  },
  {
    subject: 'Orthopaedics',
    color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    sections: [
      {
        title: 'Fractures',
        points: [
          'Colles\' fracture: distal radius; dinner fork deformity; fall on outstretched hand',
          'Smith\'s fracture: distal radius (reverse Colles); garden spade deformity',
          'Scaphoid fracture: anatomical snuffbox tenderness; risk of avascular necrosis',
          'Pott\'s fracture: bimalleolar ankle fracture; eversion injury',
          'Monteggia: proximal ulna fracture + radial head dislocation',
          'Galeazzi: distal radial fracture + distal radio-ulnar joint dislocation',
          'Compartment syndrome: severe pain + paresthesia + tense swelling; emergency fasciotomy',
        ],
      },
      {
        title: 'Joints & Spine',
        points: [
          'AVN femoral head: after neck of femur fracture, sickle cell, steroids, alcoholism',
          'Perthe\'s disease: AVN femoral head in children (4–8 years); Waldenstrom sign on X-ray',
          'SUFE (slipped upper femoral epiphysis): obese adolescent; medial displacement; ice cream falling off cone',
          'Prolapsed disc: L4-5 and L5-S1 most common; positive SLR test',
          'Spondylolisthesis: forward slip of vertebra; L5 on S1 most common',
          'OA: Heberden\'s nodes (DIP), Bouchard\'s nodes (PIP); asymmetric joint space narrowing on X-ray',
        ],
      },
    ],
  },
  {
    subject: 'Anaesthesia',
    color: 'bg-slate-100 text-slate-700 dark:bg-slate-900/40 dark:text-slate-300',
    sections: [
      {
        title: 'Inhalational & IV Agents',
        points: [
          'MAC (Minimum Alveolar Concentration): concentration for 50% of patients to not move to surgical incision; lower MAC = more potent',
          'Halothane: highest MAC reduction with N₂O; hepatotoxicity (halothane hepatitis)',
          'Desflurane: lowest blood-gas solubility (fastest induction/recovery); pungent, irritates airway',
          'Sevoflurane: pleasant smell; safe for inhalational induction in children',
          'Propofol: IV induction; anti-emetic; white emulsion; propofol infusion syndrome in prolonged use',
          'Ketamine: dissociative anaesthesia; bronchodilator; raises BP (sympathomimetic); emergence phenomena',
          'Thiopentone: ultra-short acting barbiturate; contraindicated in porphyria',
        ],
      },
      {
        title: 'Regional & Muscle Relaxants',
        points: [
          'Succinylcholine (suxamethonium): depolarising NMB; fastest onset; SE: hyperkalaemia, malignant hyperthermia',
          'Malignant hyperthermia: succinylcholine or volatile agents; ryanodine receptor mutation; treat with dantrolene',
          'Rocuronium: non-depolarising; sugammadex reverses it',
          'Neostigmine: reverses non-depolarising NMBs; give with atropine/glycopyrrolate',
          'Spinal anaesthesia: L3–L4 or L4–L5; LA below conus medullaris; total spinal if too high',
          'Bupivacaine: longest acting local anaesthetic; highest cardiotoxicity; 0.5% for spinal',
        ],
      },
    ],
  },
  {
    subject: 'Radiology',
    color: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300',
    sections: [
      {
        title: 'X-Ray Findings',
        points: [
          'Air crescent sign: aspergilloma (fungus ball in cavity)',
          'Egg-shell calcification: silicosis, sarcoidosis lymph nodes',
          'Ground-glass opacity (GGO): partial filling of alveoli; COVID-19, PCP, pulmonary oedema',
          'Honeycomb lung: end-stage pulmonary fibrosis (UIP pattern)',
          'Butterfly/bat-wing pattern: pulmonary oedema (perihilar)',
          'Steeple sign: croup (subglottic narrowing)',
          'Thumbprint sign: epiglottitis',
          'String of beads: FMD of renal artery, necrotising enterocolitis on AXR',
        ],
      },
      {
        title: 'Contrast & MRI',
        points: [
          'Barium swallow: bird beak sign → achalasia cardia',
          'Rat tail appearance: carcinoma oesophagus',
          'Apple-core lesion: carcinoma colon',
          'Cobblestone appearance: Crohn\'s disease',
          'String sign: Crohn\'s (string of Kantor) or hypertrophic pyloric stenosis',
          'MRI contraindications: pacemakers, cochlear implants, some metallic foreign bodies',
          'IV contrast contraindications: renal failure (GFR <30), metformin (hold 48h post), seafood/iodine allergy',
        ],
      },
    ],
  },
];
