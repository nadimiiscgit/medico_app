"""
Re-classify subjects for all questions using word-boundary matching
and improved keyword lists. Also normalizes naming inconsistencies.
"""
import json
import re

# Word-boundary safe keyword matching
def wbmatch(keywords, text):
    """Count how many keywords appear as whole words in text."""
    count = 0
    for kw in keywords:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            count += 1
    return count

# Improved subject keywords — NO single short ambiguous words
# All keywords must be specific enough to not appear as substrings of common words
SUBJECT_KEYWORDS = {
    'Anatomy': [
        'anatomy', 'anatomical', 'histology', 'embryology',
        'nerve supply', 'blood supply', 'artery', 'vein', 'lymphatics',
        'muscle', 'vertebra', 'thorax', 'pelvis',
        'humerus', 'femur', 'cranial nerve', 'ligament', 'tendon',
        'cartilage', 'foramen', 'fossa', 'nucleus', 'ganglion',
        'bursa', 'fascia', 'periosteum', 'endosteum',
        'epiphysis', 'diaphysis', 'condyle', 'epicondyle',
        'dermatome', 'myotome', 'sclerotome',
        'neural tube', 'notochord', 'somite', 'branchial',
        'testis', 'ovary development', 'renal development',
        'rotation of gut', 'umbilical', 'ductus arteriosus',
        'foramen ovale', 'gubernaculum', 'processus vaginalis',
    ],
    'Physiology': [
        'physiology', 'physiological',
        'cardiac output', 'stroke volume', 'ejection fraction',
        'membrane potential', 'action potential', 'resting potential',
        'renal threshold', 'glomerular filtration', 'tubular reabsorption',
        'hemoglobin', 'oxygen dissociation', 'bohr effect', 'haldane',
        'tidal volume', 'vital capacity', 'fev1', 'residual volume',
        'surfactant', 'compliance', 'dead space',
        'baroreceptor', 'chemoreceptor', 'starling', 'frank-starling',
        'hormone secretion', 'feedback inhibition', 'hypothalamus',
        'aldosterone', 'antidiuretic hormone', 'adh', 'vasopressin',
        'erythropoietin', 'renin-angiotensin', 'juxtaglomerular',
        'bile secretion', 'gastric acid', 'pepsinogen', 'secretin',
        'cholecystokinin', 'gastrin', 'motor neuron', 'neuromuscular junction',
        'reflex arc', 'stretch reflex', 'muscle spindle',
        'blood-brain barrier', 'cerebrospinal fluid',
    ],
    'Biochemistry': [
        'biochemistry', 'biochemical',
        'enzyme', 'coenzyme', 'substrate',
        'glycolysis', 'krebs cycle', 'tca cycle', 'electron transport',
        'gluconeogenesis', 'glycogenesis', 'glycogenolysis',
        'fatty acid synthesis', 'beta oxidation', 'ketone body',
        'amino acid', 'urea cycle', 'transamination', 'deamination',
        'protein synthesis', 'ribosome', 'mrna', 'trna', 'rrna',
        'dna replication', 'transcription', 'translation',
        'nucleotide', 'purine', 'pyrimidine', 'adenine', 'guanine',
        'vitamin b1', 'vitamin b2', 'vitamin b12', 'thiamine',
        'riboflavin', 'niacin', 'folate', 'folic acid', 'biotin',
        'collagen synthesis', 'elastin', 'proteoglycan',
        'heme synthesis', 'porphyrin', 'bilirubin metabolism',
        'cholesterol synthesis', 'lipoprotein', 'ldl', 'hdl',
        'restriction enzyme', 'pcr', 'recombinant dna',
        'km', 'vmax', 'michaelis-menten', 'competitive inhibition',
    ],
    'Pathology': [
        'pathology', 'pathological', 'histopathology', 'cytopathology',
        'neoplasm', 'carcinoma', 'adenocarcinoma', 'squamous cell',
        'sarcoma', 'lymphoma', 'leukemia', 'leukaemia', 'myeloma',
        'biopsy', 'frozen section', 'excision biopsy',
        'granuloma', 'caseating', 'non-caseating',
        'infarction', 'coagulative necrosis', 'liquefactive necrosis',
        'caseous necrosis', 'fibrinoid necrosis', 'fat necrosis',
        'hyperplasia', 'metaplasia', 'dysplasia', 'anaplasia',
        'malignant', 'benign', 'fibrosis', 'cirrhosis pathology',
        'abscess formation', 'thrombosis', 'embolism', 'infarct',
        'edema pathology', 'amyloid', 'hyaline',
        'cell injury', 'apoptosis', 'autophagy',
        'onion skin', 'reed-sternberg', 'psammoma body',
        'karyorrhexis', 'karyolysis', 'pyknosis',
    ],
    'Pharmacology': [
        'pharmacology', 'pharmacokinetics', 'pharmacodynamics',
        'half life', 'bioavailability', 'first pass',
        'volume of distribution', 'clearance rate',
        'agonist', 'antagonist', 'partial agonist', 'inverse agonist',
        'dose response', 'therapeutic index', 'ld50', 'ed50',
        'antibiotic', 'antifungal', 'antiviral', 'antiparasitic',
        'penicillin', 'ampicillin', 'amoxicillin', 'cephalosporin',
        'tetracycline', 'aminoglycoside', 'macrolide', 'fluoroquinolone',
        'metronidazole', 'chloramphenicol', 'vancomycin', 'rifampicin',
        'mechanism of action', 'drug resistance', 'toxicity',
        'beta blocker', 'alpha blocker', 'calcium channel blocker',
        'ace inhibitor', 'diuretic', 'antihypertensive drug',
        'nsaid', 'opioid', 'analgesic drug',
        'antiepileptic', 'anticonvulsant', 'antidepressant', 'antipsychotic',
        'insulin', 'metformin', 'sulfonylurea', 'antidiabetic drug',
        'digoxin', 'warfarin', 'heparin', 'statin',
        'oral contraceptive', 'corticosteroid therapy',
    ],
    'Microbiology': [
        'microbiology', 'microbiological',
        'bacteria', 'bacterial', 'bacterium',
        'virus', 'viral', 'virion', 'bacteriophage',
        'fungus', 'fungi', 'fungal', 'candida', 'aspergillus',
        'parasite', 'parasitic', 'protozoa',
        'gram positive', 'gram negative', 'gram stain',
        'acid fast', 'ziehl-neelsen', 'albert stain',
        'culture medium', 'agar', 'mcconkey', 'blood agar',
        'staphylococcus', 'streptococcus', 'pneumococcus',
        'mycobacterium tuberculosis', 'mycobacterium leprae',
        'escherichia coli', 'klebsiella', 'pseudomonas', 'proteus',
        'salmonella', 'shigella', 'vibrio', 'helicobacter',
        'plasmodium', 'malaria parasite', 'falciparum',
        'entamoeba', 'giardia', 'leishmania', 'trypanosoma',
        'hiv', 'hepatitis virus', 'herpes virus', 'influenza virus',
        'antigen detection', 'widal test', 'agglutination',
        'toxin', 'exotoxin', 'endotoxin', 'superantigen',
        'serology', 'elisa', 'western blot', 'pcr diagnosis',
        'opportunistic infection', 'nosocomial',
    ],
    'Medicine': [
        'hypertension', 'essential hypertension', 'secondary hypertension',
        'diabetes mellitus', 'type 1 diabetes', 'type 2 diabetes',
        'hypothyroidism', 'hyperthyroidism', 'thyrotoxicosis', 'graves disease',
        'myocardial infarction', 'angina pectoris', 'coronary artery',
        'heart failure', 'cardiac failure', 'atrial fibrillation',
        'rheumatoid arthritis', 'systemic lupus', 'sle', 'vasculitis',
        'chronic kidney disease', 'nephrotic syndrome', 'nephritic',
        'hepatitis b', 'hepatitis c', 'liver cirrhosis', 'portal hypertension',
        'anemia', 'iron deficiency', 'megaloblastic', 'hemolytic anemia',
        'lymphadenopathy', 'splenomegaly', 'hepatosplenomegaly',
        'pneumonia', 'tuberculosis', 'copd', 'asthma', 'bronchiectasis',
        'meningitis', 'encephalitis', 'stroke', 'epilepsy',
        'parkinson disease', 'multiple sclerosis',
        'peptic ulcer', 'gerd', 'inflammatory bowel disease',
        'crohn disease', 'ulcerative colitis',
        'internal medicine', 'clinical medicine',
    ],
    'Surgery': [
        'surgery', 'surgical', 'operation',
        'appendicitis', 'appendectomy',
        'hernia', 'inguinal hernia', 'femoral hernia', 'hiatus hernia',
        'laparoscopy', 'laparotomy', 'exploratory laparotomy',
        'anastomosis', 'bowel obstruction', 'intussusception',
        'colostomy', 'ileostomy', 'colectomy',
        'cholecystitis', 'cholecystectomy', 'cholelithiasis',
        'pancreatitis', 'pancreatic pseudocyst',
        'portal hypertension surgical', 'splenectomy',
        'thyroidectomy', 'parathyroidectomy',
        'mastectomy', 'breast lump', 'breast carcinoma surgery',
        'amputation', 'fasciotomy', 'debridement',
        'trauma', 'wound healing', 'keloid',
        'varicose veins', 'deep vein thrombosis surgical',
        'gastric outlet obstruction', 'peptic ulcer surgery',
        'carcinoma colon', 'carcinoma stomach surgical',
        'esophageal carcinoma', 'oesophageal',
        'fistula', 'fissure', 'fistula-in-ano', 'hemorrhoids', 'haemorrhoids',
    ],
    'Obstetrics & Gynaecology': [
        'obstetric', 'antenatal', 'prenatal', 'postnatal', 'postpartum',
        'labour', 'delivery', 'cesarean', 'caesarean', 'normal delivery',
        'antepartum hemorrhage', 'postpartum hemorrhage', 'placenta previa',
        'abruptio placentae', 'ectopic pregnancy', 'molar pregnancy',
        'pre-eclampsia', 'eclampsia', 'gestational hypertension',
        'gestational diabetes',
        'gynaecology', 'gynecology', 'gynecological',
        'cervix', 'uterus', 'ovary', 'fallopian tube',
        'menstrual cycle', 'amenorrhea', 'dysmenorrhea', 'menorrhagia',
        'polycystic ovary', 'pcos', 'endometriosis',
        'pelvic inflammatory disease', 'pid',
        'cervical carcinoma', 'endometrial carcinoma', 'ovarian cyst',
        'contraception', 'iud', 'oral contraceptive',
        'infertility', 'assisted reproduction', 'ivf',
        'preterm labour', 'preterm birth', 'premature',
        'fetal growth', 'intrauterine growth',
        'amniotic fluid', 'oligohydramnios', 'polyhydramnios',
    ],
    'Paediatrics': [
        'paediatric', 'pediatric', 'paediatrics', 'pediatrics',
        'neonatal', 'newborn', 'neonate',
        'developmental milestone', 'growth chart', 'weight gain infant',
        'vaccination schedule', 'immunization schedule', 'childhood vaccine',
        'kwashiorkor', 'marasmus', 'protein energy malnutrition',
        'intussusception child', 'pyloric stenosis',
        'congenital heart disease', 'patent ductus', 'ventricular septal',
        'atrial septal defect', 'tetralogy of fallot',
        'meningitis child', 'febrile convulsion',
        'respiratory syncytial', 'rsv', 'croup', 'whooping cough',
        'measles', 'mumps', 'chickenpox', 'rubella',
        'hemolytic disease of newborn', 'kernicterus',
        'down syndrome', 'turner syndrome', 'klinefelter',
        'rickets', 'scurvy child', 'vitamin deficiency child',
        'acute rheumatic fever', 'kawasaki disease',
        'hirschsprung', 'tracheoesophageal fistula',
    ],
    'Psychiatry': [
        'psychiatry', 'psychiatric',
        'schizophrenia', 'psychosis', 'psychotic',
        'bipolar disorder', 'manic episode', 'depressive episode',
        'major depression', 'dysthymia',
        'anxiety disorder', 'generalized anxiety', 'panic disorder',
        'obsessive compulsive', 'ocd',
        'phobia', 'social phobia', 'agoraphobia',
        'ptsd', 'post traumatic stress',
        'dementia', 'alzheimer', 'cognitive decline',
        'delirium', 'confusion state',
        'personality disorder', 'borderline personality',
        'hallucination', 'delusion', 'thought disorder',
        'antipsychotic', 'clozapine', 'haloperidol', 'risperidone',
        'electroconvulsive therapy', 'ect',
        'mental status examination', 'cognitive assessment',
        'drug dependence', 'alcohol dependence', 'withdrawal syndrome',
        'suicide risk', 'self harm',
    ],
    'Radiology': [
        'radiograph', 'x-ray finding', 'chest x-ray', 'plain film',
        'ct scan', 'computed tomography', 'mri', 'magnetic resonance',
        'ultrasound finding', 'usg', 'doppler',
        'pet scan', 'nuclear medicine', 'scintigraphy',
        'contrast study', 'barium', 'iodinated contrast',
        'opacity', 'lucency', 'calcification on imaging',
        'air bronchogram', 'pleural effusion radiology',
        'mediastinal widening', 'cardiomegaly on x-ray',
        'bone density', 'dexa scan', 'osteoporosis on xray',
        'interventional radiology', 'angiography',
        'radiation dose', 'rem', 'gray', 'sievert',
    ],
    'Orthopaedics': [
        'orthopaedic', 'orthopedic',
        'fracture', 'dislocation', 'subluxation',
        'colles fracture', 'smith fracture', 'pott fracture',
        'scaphoid fracture', 'femoral neck fracture',
        'supracondylar fracture', 'monteggia', 'galeazzi',
        'joint replacement', 'total hip', 'total knee',
        'osteomyelitis', 'septic arthritis bone',
        'osteoporosis', 'osteomalacia',
        'scoliosis', 'kyphosis', 'lordosis',
        'cervical spondylosis', 'lumbar spondylosis', 'disc prolapse',
        'sciatica', 'carpal tunnel',
        'meniscal tear', 'anterior cruciate ligament', 'acl',
        'compartment syndrome',
        'malunion', 'nonunion', 'delayed union',
        'volkmann contracture', 'sudeck atrophy',
        'bone tumor', 'osteosarcoma', 'ewing sarcoma',
        'gout', 'pseudogout', 'crystal arthropathy',
    ],
    'ENT': [
        'otology', 'otitis media', 'otitis externa',
        'tympanic membrane', 'tympanoplasty', 'mastoidectomy',
        'cochlear implant', 'hearing loss', 'conductive deafness', 'sensorineural',
        'cholesteatoma', 'ossicle',
        'rhinology', 'nasal polyp', 'deviated septum',
        'sinusitis', 'maxillary sinusitis', 'frontal sinusitis', 'epistaxis',
        'rhinitis', 'allergic rhinitis',
        'larynx', 'laryngoscopy', 'laryngectomy',
        'pharynx', 'pharyngitis', 'tonsillitis', 'tonsillectomy', 'adenoid',
        'vocal cord', 'hoarseness', 'stridor',
        'parotid', 'submandibular gland', 'salivary gland',
        'vertigo', 'meniere', 'labyrinthitis',
        'caloric test', 'audiogram', 'audiometry',
    ],
    'Ophthalmology': [
        'ophthalmology', 'ophthalmic',
        'retina', 'retinal detachment', 'retinopathy',
        'glaucoma', 'intraocular pressure',
        'cataract', 'lens opacity',
        'cornea', 'corneal ulcer', 'keratitis', 'keratoconus',
        'conjunctiva', 'conjunctivitis',
        'iris', 'iridocyclitis', 'uveitis',
        'optic nerve', 'optic neuritis', 'papilledema',
        'strabismus', 'squint', 'amblyopia',
        'visual field', 'scotoma', 'visual acuity',
        'slit lamp', 'fundoscopy', 'fundus examination',
        'pterygium', 'pinguecula',
        'dacryocystitis', 'lacrimal',
        'color blindness', 'night blindness',
        'laser photocoagulation', 'vitrectomy',
    ],
    'Dermatology': [
        'dermatology', 'dermatological', 'skin lesion',
        'psoriasis', 'eczema', 'atopic dermatitis',
        'contact dermatitis', 'allergic dermatitis',
        'melanoma', 'basal cell carcinoma', 'squamous cell skin',
        'acne vulgaris', 'rosacea',
        'vitiligo', 'alopecia', 'hair loss',
        'pemphigus', 'pemphigoid', 'bullous',
        'urticaria', 'angioedema',
        'leprosy', 'hansen disease',
        'tinea', 'ringworm', 'dermatophyte',
        'scabies', 'pediculosis',
        'sebaceous cyst', 'lipoma skin',
        'lichen planus', 'lichen sclerosus',
        'erythema multiforme', 'stevens johnson',
        'dermatomyositis', 'scleroderma skin',
    ],
    'Anaesthesia': [
        'anaesthesia', 'anesthesia', 'anaesthetic', 'anesthetic',
        'general anaesthesia', 'regional anaesthesia',
        'sedation', 'monitored anaesthesia',
        'endotracheal intubation', 'laryngeal mask airway', 'lma',
        'spinal anaesthesia', 'epidural anaesthesia',
        'brachial plexus block', 'nerve block',
        'inhalational agent', 'halothane', 'isoflurane', 'sevoflurane',
        'intravenous induction', 'propofol', 'thiopentone', 'ketamine',
        'muscle relaxant', 'suxamethonium', 'vecuronium', 'atracurium',
        'malignant hyperthermia',
        'oxygen saturation monitoring', 'capnography', 'pulse oximetry',
        'airway management', 'difficult airway',
        'pain management', 'patient controlled analgesia',
        'awake intubation', 'rapid sequence induction',
    ],
    'Forensic Medicine': [
        'forensic', 'medicolegal', 'medico-legal',
        'autopsy', 'post-mortem', 'postmortem',
        'rigor mortis', 'livor mortis', 'algor mortis',
        'cause of death', 'manner of death', 'time of death',
        'exhumation', 'inquest',
        'hanging', 'strangulation', 'asphyxia',
        'drowning', 'suffocation',
        'wound ballistics', 'gunshot wound', 'entry wound', 'exit wound',
        'blunt force', 'incised wound', 'stab wound',
        'sexual assault', 'rape examination',
        'blood alcohol', 'toxicology screen',
        'brain death', 'vegetative state legal',
        'consent', 'informed consent legal',
        'medical negligence', 'malpractice',
        'dna fingerprinting forensic',
    ],
    'Community Medicine': [
        'community medicine', 'preventive medicine', 'social medicine',
        'epidemiology', 'incidence', 'prevalence',
        'sensitivity', 'specificity', 'positive predictive value',
        'odds ratio', 'relative risk', 'risk ratio',
        'attributable risk', 'number needed to treat',
        'public health', 'national health program',
        'vaccination coverage', 'herd immunity',
        'surveillance', 'disease notification',
        'environmental health', 'water sanitation',
        'air pollution', 'occupational health',
        'nutrition survey', 'malnutrition',
        'reproductive health', 'maternal mortality', 'infant mortality',
        'disability adjusted life year', 'daly', 'qaly',
        'randomized controlled trial', 'cohort study', 'case control',
        'confounding', 'bias', 'p-value', 'confidence interval',
        'screening program', 'mass screening',
        'health education', 'primary prevention',
        'secondary prevention', 'tertiary prevention',
    ],
}

def infer_subject_improved(question: str, options_text: str = '') -> tuple[str, int]:
    """Returns (subject, match_count). 'General Medicine' with count=0 means unclassified."""
    full_text = (question + ' ' + options_text).lower()
    best_subject = 'General Medicine'
    best_count = 0

    for subject, keywords in SUBJECT_KEYWORDS.items():
        count = wbmatch(keywords, full_text)
        if count > best_count:
            best_count = count
            best_subject = subject

    return best_subject, best_count


# Normalize subject names from 2022-2023 explicit metadata
SUBJECT_NORMALIZE = {
    'Gynaecology & Obstetrics': 'Obstetrics & Gynaecology',
    'Gynaecology & Obstetrircs': 'Obstetrics & Gynaecology',
    'Pediatrics': 'Paediatrics',
    'PSM': 'Community Medicine',
    'General Medicine': 'Medicine',  # Only for 2022-2023 explicit ones
}

def normalize_subject(subj: str, is_explicit: bool) -> str:
    if is_explicit:
        # For 2022-2023 where subject came from PDF
        return SUBJECT_NORMALIZE.get(subj, subj)
    return subj  # Will be re-inferred


if __name__ == '__main__':
    with open('/Users/nadims_mac/Desktop/medico_pyq_app/data/extracted/questions.json') as f:
        qs = json.load(f)

    print(f'Loaded {len(qs)} questions')

    # Years with explicit subject metadata from PDF (format_c)
    EXPLICIT_YEARS = {2022, 2023}

    updated = 0
    unclassified = 0

    for q in qs:
        options_text = ' '.join(q.get('options', {}).values())
        is_explicit = q['year'] in EXPLICIT_YEARS

        if is_explicit:
            # Just normalize the name
            new_subj = SUBJECT_NORMALIZE.get(q['subject'], q['subject'])
        else:
            # Re-infer with improved classifier
            opts_text = options_text
            new_subj, count = infer_subject_improved(q['question'], opts_text)
            if count == 0:
                unclassified += 1

        if new_subj != q['subject']:
            updated += 1

        q['subject'] = new_subj

    print(f'Updated subjects: {updated}')
    print(f'Still unclassified (General Medicine fallback): {unclassified}')

    from collections import Counter
    subj_counts = Counter(q['subject'] for q in qs)
    print('\n=== New subject distribution ===')
    for s, c in sorted(subj_counts.items(), key=lambda x: -x[1]):
        print(f'  {s}: {c} ({c/len(qs)*100:.1f}%)')

    with open('/Users/nadims_mac/Desktop/medico_pyq_app/data/extracted/questions.json', 'w') as f:
        json.dump(qs, f, ensure_ascii=False, separators=(',', ':'))

    import shutil
    shutil.copy(
        '/Users/nadims_mac/Desktop/medico_pyq_app/data/extracted/questions.json',
        '/Users/nadims_mac/Desktop/medico_pyq_app/medico-app/public/questions.json'
    )
    print('\nSaved and copied to public/')
