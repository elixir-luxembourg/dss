START_UP_DATA = {'ga4gh_codes': [['NRES', 'No restrictions', 'No restrictions on data use.'],
                                 ['GRU(CC)', 'General Research use and Clinical Care',
                                  'For health/medical/biomedical purposes and other biological research, including the study of population origins or ancestry.'],
                                 ['HMB(CC)', 'Health/medical/biomedical Research and Clinical Care',
                                  'Use of the data is limited to health/medical/biomedical purposes, does not include the study of population origins or ancestry.'],
                                 ['DS-[XX](CC)', 'Disease-specific Research and Clinical Care.',
                                  'Use of the data must be related to [disease].'],
                                 ['POA', 'Population Origins/Ancestry research',
                                  'Use of the data is limited to the study of population origins or ancestry.'],
                                 ['RS-[XX]', 'Other Research-specific restrictions',
                                  'Use of the data is limited to studies of [research type] (e.g., pediatric research).'],
                                 ['RUO', 'Research Use Only',
                                  'Use of data is limited to research purposes (e.g., does not include its use in clinical care).'],
                                 ['NMDS', 'No \"General Methods\" Research',
                                  'Use of the data includes methods development research (e.g., development of software or algorithms) ONLY within the bounds of other data use limitations.'],
                                 ['GSO', 'Genetic Studies Only',
                                  'Use of the data is limited to genetic studies only (i.e., no research using only the phenotype data).'],
                                 ['NPU', 'Not-for-profit Use Only',
                                  'Use of the data is limited to not-for-profit organizations.'],
                                 ['PUB', 'Publication Required',
                                  'Requestor agrees to make results of studies using the data available to the larger scientific community.'],
                                 ['COL-[XX]', 'Collaboration Required',
                                  'Requestor must agree to collaboration with the primary study investigator(s).'],
                                 ['RTN', 'Return data to database/resource',
                                  'Requestor must return derived/enriched data to the database/resource.'],
                                 ['IRB', 'Ethics Approval Required',
                                  'Requestor must provide documentation of local IRB/REC approval.'],
                                 ['GS-[XX]', 'Geographical Restrictions',
                                  'Use of the data is limited to within [geographic region].'],
                                 ['MOR-[XX]', 'Publication Moratorium/Embargo',
                                  'Requestor agrees not to publish results of studies until [date].'],
                                 ['TS-[XX]', 'Time Limits on use', 'Use of data is approved for [x months].'],
                                 ['US', 'User-Specific restrictions',
                                  'Use of data is limited to use by approved users.'],
                                 ['PS', 'Project-Specific restrictions',
                                  'Use of data is limited to use within an approved project.'],
                                 ['IS', 'Institution-Specific restrictions',
                                  'Use of data is limited to use within an approved institution.']],
                 'contact_types': ['Principal_Investigator', 'Researcher', 'Data_Manager', 'Data_Protection_Officer',
                                   'Legal_Representative', 'Other'],
                 'names_roles': ['data_provider', 'admin'],
                 'size_categories': [['s', 'Less than 10GB'],
                                     ['m', 'Between 10 and 100GB'],
                                     ['l', 'Greater than 100 GB']],
                 'deidentification_type': [['p', 'Pseudonymized'],
                                           ['a', 'Anonymized']],
                 'consent_status': [['m', 'Homogeneous'],
                                    ['t', 'Heterogeneous']],
                 'legal_basis': [['c', 'Consent'],
                                 ['l', 'Legitimate_Interest'],
                                 ['p', 'Public_Interest']],
                 'submission_scope': [['e', 'ELIXIR-LU Repository'],
                                      ['c', 'LCSB Collaborator']],

                 'data_types': (
                     ('Samples', 'Samples'),
                     ('Genotype_data', (
                         ('Whole_genome_sequencing', 'Whole_genome_sequencing'),
                         ('Exome_sequencing', 'Exome_sequencing'),
                         ('Genomics_variant_array', 'Genomics_variant_array'),
                         ('RNASeq', 'RNASeq')
                     )),
                     ('Genetic_and_derived_genetic_data', (
                         ('Transcriptome_array', 'Transcriptome_array'),
                         ('Methylation_array', 'Methylation_array'),
                         ('MicroRNA_array', 'MicroRNA_array'),
                         ('Metabolomics', 'Metabolomics'),
                         ('Proteomics', 'Proteomics'),
                         ('Other_omics_data', 'Other_omics_data'),

                     )),
                     ('Imaging', (
                         ('Clinical_Imaging', 'Clinical_Imaging'),
                         ('Cell_Imaging', 'Cell_Imaging')
                     )),
                     ('Human_subject_data', (
                         ('Clinical_data', 'Clinical_data'),
                         ('Lifestyle_data', 'Lifestyle_data'),
                         ('Socio_Economic_Data', 'Socio_Economic_Data'),
                         ('Other_Phenotype_data', 'Other_Phenotype_data')
                     )),
                     ('Other', 'Other')
                 ),
                 'study_types': [
                     "Observational",
                     "Interventional",
                     "Expanded_Access",
                     "Longitudinal_Cohort",
                     "Cross_Sectional",
                     "Case_Control",
                     "Case_Set",
                     "Control_Set",
                     "Parent_Offspring",
                     "Unrelated_Individuals",
                     "Sibling_Pairs",
                     "Family",
                     "Pedigree",
                     "Preclinical_Trial",
                     "Clinical_Trial",
                     "Meta_Analysis",
                     "Prospective",
                     "Retrospective",
                     "Phase_I",
                     "Phase_II",
                     "Phase_III",
                     "Phase_IV",
                     "Single_Group",
                     "Parallel",
                     "Cross_Over",
                     "Factorial",
                     "Randomized",
                     "Blind",
                     "Controlled",
                     "Open",
                     "Single_Blind",
                     "Double_Blind"
                 ],
                 'cohorts': [
                     {
                         "elu_accession": "ELU_C_1",
                         "title": "LuxPARK",
                         "ombudsman": [
                             "Rejko Kr\u00fcger"
                         ],
                         "comments": "HELP-PD will establish a state-of-the-art cohort project of patients with parkinsonism in Luxembourg to identify predictive and progression markers of the disease.  Thereby this project provides a unique infrastructure and resource for innovative clinical research in Luxembourg. The cohort program integrates an informative design (patient cohorts as well as risk cohorts in Phase II), a detailed neurological examination and structured assessment of epidemiological, neuropsychological and other clinical features, a comprehensive collection of biosamples and an integrated, anonymized data repository with web-based access. Initially, a cross-sectional assessment aimed at all diagnosed PD cases in Luxembourg will be performed, establishing a foundation for the PD registry. Subsequently, patients with PD will be followed up longitudinally.",
                         "institutes": [
                             "ELU_I_77",
                             "ELU_I_9",
                             "ELU_I_1",
                             "ELU_I_79"
                         ]
                     },
                     {
                         "elu_accession": "ELU_C_2",
                         "title": "MUST (Diabetes MUltiplex family STudy)",
                         "ombudsman": [
                             "Carine de Beaufort"
                         ],
                         "comments": "The MUST study (Diabetes MUltiplex family STudy) is initiated by the Personalised Medicine Consortium of Luxembourg in an effort to bring together clinicians and researchers to drive clinical innovation that ultimately benefits diabetes patients.",
                         "institutes": [
                             "ELU_I_9",
                             "ELU_I_77",
                             "ELU_I_1"
                         ]
                     },
                     {
                         "elu_accession": "ELU_C_3",
                         "title": "COSMIC (Colonisation, Succession and Evolution of Human Gastrointestinal Microbiome from Birth to Infancy)",
                         "ombudsman": [
                             "Carine de Beaufort"
                         ],
                         "comments": "COSMIC will look more precisely at how the gut microflora develops immediately after birth and how this may influence the development of diabetes later in life.  For this study, the genetics and bacterial populations of healthy neonates and neonates at high risk to develop adult metabolic disease (e.g. diabetes) due to family history or low birth weight will be compared to those of their mothers. Information gained from these studies could provide the basis for later interventional studies looking at the modification of nutrition and the use of bacterial supplements in at-risk groups.",
                         "institutes": [
                             "ELU_I_9",
                             "ELU_I_77",
                             "ELU_I_1"
                         ]
                     },
                     {
                         "elu_accession": "ELU_C_4",
                         "title": "DeNoPa (De Novo Parkinson Longitudinal Study)",
                         "ombudsman": [
                             "Brit Mollenhauer"
                         ],
                         "comments": "DeNoPa study is led by Prof. Britt Mollenhauer at Paracelsus Elena Hospital in Kassel. ...",
                         "institutes": [
                             "ELU_I_51"
                         ]
                     },
                     {
                         "elu_accession": "ELU_C_5",
                         "title": "TREND (T\u00fbbinger evaluation of Risk factors for Early detection of NeuroDegeneration.)",
                         "ombudsman": [
                             "Daniela Berg"
                         ],
                         "comments": "The occurrence of specific symptoms that allow the clinical diagnosis of Parkinson's and Alzheimer's disease is preceded by a long prodromal phase in which the neurodegenerative process leads to substantial neuronal loss. To enable earlier intervention or even neuroprotective therapy it is essential to identify, characterize and validate risk and prodromal markers for Parkinson’s and Alzheimer’s disease. Approx. 1200 individuals with a specific risk profile aged over 50 years at baseline are biannually assessed by a comprehensive, quantitative assessment battery to meet these aims.",
                         "institutes": [
                             "ELU_I_61"
                         ]
                     },
                     {
                         "elu_accession": "ELU_C_6",
                         "title": "ADNI (Alzheimer's Disease Neuroimaging Initiative.)",
                         "comments": "...TBD...",
                         "institutes": [
                             "ELU_I_84"
                         ]
                     },
                     {
                         "elu_accession": "ELU_C_7",
                         "title": "PPMI (Parkinsons Progressive Markers Inititative Study Cohort.)",
                         "comments": "...TBD...",
                         "institutes": [
                             "ELU_I_85"
                         ]
                     },
                     {
                         "elu_accession": "ELU_C_8",
                         "title": "Supercentenarians (Betterhumans Inc. Supercentenarians Research Study)",
                         "comments": "...TBD...",
                         "institutes": [
                             "ELU_I_54"
                         ]
                     }
                 ],
                 'collab_institutions': [
                     {
                         "elu_accession": "ELU_I_1",
                         "name": "Integrated Biobank of Luxembourg",
                         "geo_category": "National",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "IBBL"
                     },
                     {
                         "elu_accession": "ELU_I_2",
                         "name": "European Molecular Biology Laboratory",
                         "geo_category": "International",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "EMBL"
                     },
                     {
                         "elu_accession": "ELU_I_3",
                         "name": "Erasmus Hospital Brussels",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_4",
                         "name": "Erasmus University Medical Center",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True,
                         "acronym": "Erasmus MC"
                     },
                     {
                         "elu_accession": "ELU_I_5",
                         "name": "August Pi i Sunyer Biomedical Research Institute",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "IDIBAPS"
                     },
                     {
                         "elu_accession": "ELU_I_6",
                         "name": "University Hospital of the Saarland",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True,
                         "acronym": "UKS Homburg"
                     },
                     {
                         "elu_accession": "ELU_I_7",
                         "name": "University Medical Center Utrecht",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True,
                         "acronym": "UMC Utrecht"
                     },
                     {
                         "elu_accession": "ELU_I_8",
                         "name": "University of Tübingen",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC"
                     },
                     {
                         "elu_accession": "ELU_I_9",
                         "name": "Centre Hospitalier de Luxembourg",
                         "geo_category": "National",
                         "sector_category": "PUBLIC",
                         "is_clinical": True,
                         "acronym": "CHL"

                     },
                     {
                         "elu_accession": "ELU_I_10",
                         "name": "Charité University Hospital Berlin",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_11",
                         "name": "Cologne Center for Genomics",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "CCG"
                     },
                     {
                         "elu_accession": "ELU_I_12",
                         "name": "23andMe Company",
                         "geo_category": "Non_EU",
                         "sector_category": "PRIVATE_P",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_13",
                         "name": "Fraunhofer Institute for Algorithms and Scientific Computing",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "Fraunhofer SCAI"
                     },
                     {
                         "elu_accession": "ELU_I_14",
                         "name": "Karolinska Institute",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_15",
                         "name": "Boehringer Ingelheim International GmbH",
                         "geo_category": "EU",
                         "sector_category": "PRIVATE_P",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_16",
                         "name": "Union Chimique Belge Biopharma",
                         "geo_category": "EU",
                         "sector_category": "PRIVATE_P",
                         "is_clinical": False,
                         "acronym": "UCB"
                     },
                     {
                         "elu_accession": "ELU_I_17",
                         "name": "Brain and Spine Institute",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "ICM"
                     },
                     {
                         "elu_accession": "ELU_I_18",
                         "name": "Alstem LLC",
                         "geo_category": "Non_EU",
                         "sector_category": "PRIVATE_P",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_19",
                         "name": "Baylor College of Medicine",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_20",
                         "name": "Biomedical Research Foundation Academy Of Athens",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "BRFAA"
                     },
                     {
                         "elu_accession": "ELU_I_21",
                         "name": "Brazilian Institute of Neuroscience and Neurotechnology",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "BRAINN"
                     },
                     {
                         "elu_accession": "ELU_I_22",
                         "name": "Centre Hospitalier Emile Mayrisch",
                         "geo_category": "National",
                         "sector_category": "PUBLIC",
                         "is_clinical": True,
                         "acronym": "CHEM"
                     },
                     {
                         "elu_accession": "ELU_I_23",
                         "name": "Charité – Universitätsmedizin Berlin",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_24",
                         "name": "Children's Hospital of Philadelphia",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_25",
                         "name": "Cornell University",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_26",
                         "name": "Corriell Institute for Medical Research",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_27",
                         "name": "European Bank for induced pluripotent Stem Cells",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "EBiSC"
                     },
                     {
                         "elu_accession": "ELU_I_28",
                         "name": "Duke University",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_29",
                         "name": "Columbia University",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_30",
                         "name": "Oxford Parkinson's Disease Centre",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "OPDC"
                     },
                     {
                         "elu_accession": "ELU_I_31",
                         "name": "Giannina Gaslini Institute",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "Gaslini Biobank"
                     },
                     {
                         "elu_accession": "ELU_I_32",
                         "name": "Thermo Fisher Scientific",
                         "sector_category": "PRIVATE_P",
                         "is_clinical": False,
                         "geo_category": "Non_EU"
                     },
                     {
                         "elu_accession": "ELU_I_33",
                         "name": "Griffith Institute for Drug Discovery",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "GRIDD"
                     },
                     {
                         "elu_accession": "ELU_I_34",
                         "name": "Institute of Ophthalmic Research - Tübingen",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_35",
                         "name": "Luxembourg Institute of Science and Technology",
                         "geo_category": "National",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "LIST"
                     },
                     {
                         "elu_accession": "ELU_I_36",
                         "name": "Life Sciences Research Unit - University of Luxembourg",
                         "geo_category": "National",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "LSRU"
                     },
                     {
                         "elu_accession": "ELU_I_37",
                         "name": "Luxembourg Red Cross",
                         "geo_category": "National",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_38",
                         "name": "Michael J. Fox Foundation for Parkinson's Research",
                         "geo_category": "Non_EU",
                         "sector_category": "PRIVATE_NP",
                         "is_clinical": False,
                         "acronym": "MJFF"
                     },
                     {
                         "elu_accession": "ELU_I_39",
                         "name": "Maastricht University",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_40",
                         "name": "Magdeburg University Hospital",
                         "sector_category": "PUBLIC",
                         "is_clinical": True,
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_41",
                         "name": "Max Planck Society",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_42",
                         "name": "Max Rubner-Institut",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "geo_category": "EU",
                         "acronym": "MRI"
                     },
                     {
                         "elu_accession": "ELU_I_43",
                         "name": "Mayo Clinic",
                         "sector_category": "PRIVATE_NP",
                         "is_clinical": True,
                         "geo_category": "Non_EU"
                     },
                     {
                         "elu_accession": "ELU_I_44",
                         "name": "London School of Hygiene & Tropical Medicine, Medical Research Council  Unit The Gambia",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "LSHTM MRU The Gambia"
                     },
                     {
                         "elu_accession": "ELU_I_45",
                         "name": "Murdoch Children's Research Institute",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True,
                         "acronym": "MCRI"
                     },
                     {
                         "elu_accession": "ELU_I_46",
                         "name": "National Institute on Aging",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "NIA"
                     },
                     {
                         "elu_accession": "ELU_I_47",
                         "name": "National Institutes of Health",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "NIH"
                     },
                     {
                         "elu_accession": "ELU_I_48",
                         "name": "Newcastle University",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_49",
                         "name": "Norwegian University of Science and Technology",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "NTNU"
                     },
                     {
                         "elu_accession": "ELU_I_50",
                         "name": "Ohio State University Comprehensive Cancer Center",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "OSUCCC – James"
                     },
                     {
                         "elu_accession": "ELU_I_51",
                         "name": "Paracelsus-Elena-Klinik",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_52",
                         "name": "Royal College of Surgeons - Ireland",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_53",
                         "name": "Sage Bionetworks",
                         "geo_category": "Non_EU",
                         "sector_category": "PRIVATE_NP",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_54",
                         "name": "Betterhumans Inc. Supercentenarians Research Study",
                         "geo_category": "Non_EU",
                         "sector_category": "PRIVATE_NP",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_55",
                         "name": "Technical University Dresden",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "TU Dresden"
                     },
                     {
                         "elu_accession": "ELU_I_56",
                         "name": "University Hospital of Würzburg",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_57",
                         "name": "University Hospital Bonn",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True,
                         "acronym": "UKB"
                     },
                     {
                         "elu_accession": "ELU_I_58",
                         "name": "University College London",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "UCL"
                     },
                     {
                         "elu_accession": "ELU_I_59",
                         "name": "University Hospital Cologne",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_60",
                         "name": "University of Luxembourg",
                         "geo_category": "National",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_61",
                         "name": "University Hospital Tübingen",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_62",
                         "name": "University of Lübeck",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_63",
                         "name": "University Medical Center Göttingen",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_64",
                         "name": "Philipps University - Marburg",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_65",
                         "name": "University of Trier",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_66",
                         "name": "University Hospital Kiel",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True,
                         "acronym": "UKSH"
                     },
                     {
                         "elu_accession": "ELU_I_67",
                         "name": "University of Adelaide",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_68",
                         "name": "University of Eastern Finland",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "UiO"
                     },
                     {
                         "elu_accession": "ELU_I_69",
                         "name": "University of Melbourne",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_70",
                         "name": "University of Vienna",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_71",
                         "name": "University of Oslo",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "UiO"
                     },
                     {
                         "elu_accession": "ELU_I_72",
                         "name": "Uppsala University",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_73",
                         "name": "University Hospital Salzburg",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True,
                         "acronym": "SALK"
                     },
                     {
                         "elu_accession": "ELU_I_74",
                         "name": "Wellcome Sanger Institute",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_75",
                         "name": "Zithaklinik - Hôpitaux Robert Schuman",
                         "geo_category": "National",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_76",
                         "name": "Broad Institute",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_77",
                         "name": "Luxembourg Centre for Systems Biomedicine",
                         "geo_category": "National",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "LCSB"
                     },
                     {
                         "elu_accession": "ELU_I_78",
                         "name": "Chemical Sciences Division - Oak Ridge National Library",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "ORNL"
                     },
                     {
                         "elu_accession": "ELU_I_79",
                         "name": "Luxembourg institute of health",
                         "geo_category": "National",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "Lih"
                     },
                     {
                         "elu_accession": "ELU_I_80",
                         "name": "INNAXIS Research Institute",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "INNAXIS"
                     },
                     {
                         "elu_accession": "ELU_I_81",
                         "name": "SciCross AB",
                         "sector_category": "PRIVATE_P",
                         "is_clinical": False,
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_82",
                         "name": "University of California -  San Francisco",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "UCSF"
                     },
                     {
                         "elu_accession": "ELU_I_83",
                         "name": "The database of Genotypes and Phenotypes",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "dbGaP"
                     },
                     {
                         "elu_accession": "ELU_I_84",
                         "name": "Alzheimer's Disease Neuroimaging Initiative",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "ADNI"
                     },
                     {
                         "elu_accession": "ELU_I_85",
                         "name": "Parkinson's Progressive Markers Initiative",
                         "geo_category": "Non_EU",
                         "sector_category": "PRIVATE_NP",
                         "is_clinical": False,
                         "acronym": "PPMI"
                     },
                     {
                         "elu_accession": "ELU_I_86",
                         "name": "Gene Expression Omnibus",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "GEO"
                     },
                     {
                         "elu_accession": "ELU_I_87",
                         "name": "Jena University Hospital",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_88",
                         "name": "University Hospital of Geneva",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_89",
                         "name": "Braunschweig University of Technology",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_90",
                         "name": "Hummingbird Diagnostics Heidelberg",
                         "geo_category": "EU",
                         "sector_category": "PRIVATE_P",
                         "is_clinical": False
                     },
                     {
                         "elu_accession": "ELU_I_91",
                         "name": "Helmholtz Zentrum München",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "HMGU"
                     },
                     {
                         "elu_accession": "ELU_I_92",
                         "name": "German Cancer Research Center Heidelberg",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "DKFZ"
                     },
                     {
                         "elu_accession": "ELU_I_93",
                         "name": "National Cancer Institute",
                         "geo_category": "Non_EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False,
                         "acronym": "NCI"
                     },
                     {
                         "elu_accession": "ELU_I_94",
                         "name": "Hospital General Universitario de Alicante",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": True
                     },
                     {
                         "elu_accession": "ELU_I_95",
                         "name": "University of Konstanz",
                         "geo_category": "EU",
                         "sector_category": "PUBLIC",
                         "is_clinical": False
                     }
                 ],
                 'lcsb_pis': ['Reinhard Schneider',
                              'Enrico Glaab',
                              'Rudi Balling',
                              'Antonio del Sol',
                              'Jens Schwamborn',
                              'Paul Wilmes',
                              'Emma Schymanski',
                              'Ines Thiele',
                              'Jorge Goncalves',
                              'Rejko Krüger',
                              'Jochen Schneider',
                              'Anne Grünewald',
                              'Michel Mittelbronn',
                              'Alexander Skupin',
                              'Frank Hertel',
                              'Carole Linster']
                 }
