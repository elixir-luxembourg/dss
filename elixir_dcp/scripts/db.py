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
                 'contact_types': ['PI', 'Researcher', 'Data_Manager', 'Data_Protection_Officer',
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
                 'submission_scope': [['e', 'ELIXIR'],
                                      ['c', 'LCSB_Collaboration']],

                 'data_types': (
                    ('Genotype_data', (
                        ('Whole_genome_sequencing', 'Whole_genome_sequencing'),
                        ('Exome_sequencing', 'Exome_sequencing'),
                        ('Genomics_variant_array', 'Genomics_variant_array'),
                        ('RNASeq', 'RNASeq')
                    )),
                    ('Genetic and derived genetic_data', (
                        ('Transcriptome_array', 'Transcriptome_array'),
                        ('Methylation_array', 'Methylation_array'),
                        ('MicroRNA_array', 'MicroRNA_array'),
                        ('Metabolomics', 'Metabolomics'),
                        ('Proteomics', 'Proteomics'),
                        ('Other_omics_data', 'Other_omics_data'),

                    )),
                   ('Clinical_Imaging', ()),
                   ('Cell_Imaging', ()),
                    ('Human_subject_data', (
                        ('Clinical_data', 'Clinical_data'),
                        ('Lifestyle_data', 'Lifestyle_data'),
                        ('Socio_Economic_Data', 'Socio_Economic_Data')
                    )),
                       ('Others', ())
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
                 'collab_institutions': [
                     {
                         "elu_accession": "ELU_I_1",
                         "institution_name": "Integrated Biobank of Luxembourg",
                         "geo_category": "National",
                         "acronym": "IBBL"
                     },
                     {
                         "elu_accession": "ELU_I_2",
                         "institution_name": "European Molecular Biology Laboratory",
                         "geo_category": "Non-EU",
                         "acronym": "EMBL"
                     },
                     {
                         "elu_accession": "ELU_I_3",
                         "institution_name": "Erasmus Hospital Brussels",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_4",
                         "institution_name": "Erasmus University Medical Center",
                         "geo_category": "EU",
                         "acronym": "Erasmus MC"
                     },
                     {
                         "elu_accession": "ELU_I_5",
                         "institution_name": "August Pi i Sunyer Biomedical Research Institute",
                         "geo_category": "EU",
                         "acronym": "IDIBAPS"
                     },
                     {
                         "elu_accession": "ELU_I_6",
                         "institution_name": "University Hospital of the Saarland",
                         "geo_category": "EU",
                         "acronym": "UKS Homburg"
                     },
                     {
                         "elu_accession": "ELU_I_7",
                         "institution_name": "University Medical Center Utrecht",
                         "geo_category": "EU",
                         "acronym": "UMC Utrecht"
                     },
                     {
                         "elu_accession": "ELU_I_8",
                         "institution_name": "University of Tübingen",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_9",
                         "institution_name": "Centre Hospitalier de Luxembourg",
                         "geo_category": "National",
                         "acronym": "CHL"

                     },
                     {
                         "elu_accession": "ELU_I_10",
                         "institution_name": "Charité University Hospital Berlin",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_11",
                         "institution_name": "Cologne Center for Genomics",
                         "geo_category": "EU",
                         "acronym": "CCG"
                     },
                     {
                         "elu_accession": "ELU_I_12",
                         "institution_name": "23andMe Company",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_13",
                         "institution_name": "Fraunhofer Institute for Algorithms and Scientific Computing",
                         "geo_category": "EU",
                         "acronym": "Fraunhofer SCAI"
                     },
                     {
                         "elu_accession": "ELU_I_14",
                         "institution_name": "Karolinska Institute",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_15",
                         "institution_name": "Boehringer Ingelheim International GmbH",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_16",
                         "institution_name": "Union Chimique Belge Biopharma",
                         "geo_category": "EU",
                         "acronym": "UCB"
                     },
                     {
                         "elu_accession": "ELU_I_17",
                         "institution_name": "Brain and Spine Institute",
                         "geo_category": "EU",
                         "acronym": "ICM"
                     },
                     {
                         "elu_accession": "ELU_I_18",
                         "institution_name": "Alstem LLC",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_19",
                         "institution_name": "Baylor College of Medicine",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_20",
                         "institution_name": "Biomedical Research Foundation Academy Of Athens",
                         "geo_category": "EU",
                         "acronym": "BRFAA"
                     },
                     {
                         "elu_accession": "ELU_I_21",
                         "institution_name": "Brazilian Institute of Neuroscience and Neurotechnology",
                         "geo_category": "Non-EU",
                         "acronym": "BRAINN"
                     },
                     {
                         "elu_accession": "ELU_I_22",
                         "institution_name": "Centre Hospitalier Emile Mayrisch",
                         "geo_category": "National",
                         "acronym": "CHEM"
                     },
                     {
                         "elu_accession": "ELU_I_23",
                         "institution_name": "Charité – Universitätsmedizin Berlin",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_24",
                         "institution_name": "Children's Hospital of Philadelphia",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_25",
                         "institution_name": "Cornell University",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_26",
                         "institution_name": "Corriell Institute for Medical Research",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_27",
                         "institution_name": "European Bank for induced pluripotent Stem Cells",
                         "geo_category": "Non-EU",
                         "acronym": "EBiSC"
                     },
                     {
                         "elu_accession": "ELU_I_28",
                         "institution_name": "Duke University",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_29",
                         "institution_name": "Columbia University",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_30",
                         "institution_name": "Oxford Parkinson's Disease Centre",
                         "geo_category": "EU",
                         "acronym": "OPDC"
                     },
                     {
                         "elu_accession": "ELU_I_31",
                         "institution_name": "Giannina Gaslini Institute",
                         "geo_category": "EU",
                         "acronym": "Gaslini Biobank"
                     },
                     {
                         "elu_accession": "ELU_I_32",
                         "institution_name": "Thermo Fisher Scientific",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_33",
                         "institution_name": "Griffith Institute for Drug Discovery",
                         "geo_category": "Non-EU",
                         "acronym": "GRIDD"
                     },
                     {
                         "elu_accession": "ELU_I_34",
                         "institution_name": "Institute of Ophthalmic Research - Tübingen",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_35",
                         "institution_name": "Luxembourg Institute of Science and Technology",
                         "geo_category": "National",
                         "acronym": "LIST"
                     },
                     {
                         "elu_accession": "ELU_I_36",
                         "institution_name": "Life Sciences Research Unit - University of Luxembourg",
                         "geo_category": "National",
                         "acronym": "LSRU"
                     },
                     {
                         "elu_accession": "ELU_I_37",
                         "institution_name": "Luxembourg Red Cross",
                         "geo_category": "National"
                     },
                     {
                         "elu_accession": "ELU_I_38",
                         "institution_name": "Michael J. Fox Foundation for Parkinson's Research",
                         "geo_category": "Non-EU",
                         "acronym": "MJFF"
                     },
                     {
                         "elu_accession": "ELU_I_39",
                         "institution_name": "Maastricht University",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_40",
                         "institution_name": "Magdeburg University Hospital",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_41",
                         "institution_name": "Max Planck Society",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_42",
                         "institution_name": "Max Rubner-Institut",
                         "geo_category": "EU",
                         "acronym": "MRI"
                     },
                     {
                         "elu_accession": "ELU_I_43",
                         "institution_name": "Mayo Clinic",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_44",
                         "institution_name": "London School of Hygiene & Tropical Medicine, Medical Research Council  Unit The Gambia",
                         "geo_category": "EU",
                         "acronym": "LSHTM MRU The Gambia"
                     },
                     {
                         "elu_accession": "ELU_I_45",
                         "institution_name": "Murdoch Children's Research Institute",
                         "geo_category": "Non-EU",
                         "acronym": "MCRI"
                     },
                     {
                         "elu_accession": "ELU_I_46",
                         "institution_name": "National Institute on Aging",
                         "geo_category": "Non-EU",
                         "acronym": "NIA"
                     },
                     {
                         "elu_accession": "ELU_I_47",
                         "institution_name": "National Institutes of Health",
                         "geo_category": "Non-EU",
                         "acronym": "NIH"
                     },
                     {
                         "elu_accession": "ELU_I_48",
                         "institution_name": "Newcastle University",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_49",
                         "institution_name": "Norwegian University of Science and Technology",
                         "geo_category": "Non-EU",
                         "acronym": "NTNU"
                     },
                     {
                         "elu_accession": "ELU_I_50",
                         "institution_name": "Ohio State University Comprehensive Cancer Center",
                         "geo_category": "Non-EU",
                         "acronym": "OSUCCC – James"
                     },
                     {
                         "elu_accession": "ELU_I_51",
                         "institution_name": "Paracelsus-Elena-Klinik",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_52",
                         "institution_name": "Royal College of Surgeons - Ireland",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_53",
                         "institution_name": "Sage Bionetworks",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_54",
                         "institution_name": "Betterhumans Inc. Supercentenarians Research Study",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_55",
                         "institution_name": "Technical University Dresden",
                         "geo_category": "EU",
                         "acronym": "TU Dresden"
                     },
                     {
                         "elu_accession": "ELU_I_56",
                         "institution_name": "University Hospital of Würzburg",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_57",
                         "institution_name": "University Hospital Bonn",
                         "geo_category": "EU",
                         "acronym": "UKB"
                     },
                     {
                         "elu_accession": "ELU_I_58",
                         "institution_name": "University College London",
                         "geo_category": "EU",
                         "acronym": "UCL"
                     },
                     {
                         "elu_accession": "ELU_I_59",
                         "institution_name": "University Hospital Cologne",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_60",
                         "institution_name": "University of Luxembourg",
                         "geo_category": "National"
                     },
                     {
                         "elu_accession": "ELU_I_61",
                         "institution_name": "University Hospital Tübingen",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_62",
                         "institution_name": "University of Lübeck",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_63",
                         "institution_name": "University Medical Center Göttingen",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_64",
                         "institution_name": "Philipps University - Marburg",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_65",
                         "institution_name": "University of Trier",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_66",
                         "institution_name": "University Hospital Kiel",
                         "geo_category": "EU",
                         "acronym": "UKSH"
                     },
                     {
                         "elu_accession": "ELU_I_67",
                         "institution_name": "University of Adelaide",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_68",
                         "institution_name": "University of Eastern Finland",
                         "geo_category": "EU",
                         "acronym": "UiO"
                     },
                     {
                         "elu_accession": "ELU_I_69",
                         "institution_name": "University of Melbourne",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_70",
                         "institution_name": "University of Vienna",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_71",
                         "institution_name": "University of Oslo",
                         "geo_category": "Non-EU",
                         "acronym": "UiO"
                     },
                     {
                         "elu_accession": "ELU_I_72",
                         "institution_name": "Uppsala University",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_73",
                         "institution_name": "University Hospital Salzburg",
                         "geo_category": "EU",
                         "acronym": "SALK"
                     },
                     {
                         "elu_accession": "ELU_I_74",
                         "institution_name": "Wellcome Sanger Institute",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_75",
                         "institution_name": "Zithaklinik - Hôpitaux Robert Schuman",
                         "geo_category": "National"
                     },
                     {
                         "elu_accession": "ELU_I_76",
                         "institution_name": "Broad Institute",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_77",
                         "institution_name": "Luxembourg Centre for Systems Biomedicine",
                         "geo_category": "National",
                         "acronym": "LCSB"
                     },
                     {
                         "elu_accession": "ELU_I_78",
                         "institution_name": "Chemical Sciences Division - Oak Ridge National Library",
                         "geo_category": "Non-EU",
                         "acronym": "ORNL"
                     },
                     {
                         "elu_accession": "ELU_I_79",
                         "institution_name": "Luxembourg institute of health",
                         "geo_category": "National",
                         "acronym": "Lih"
                     },
                     {
                         "elu_accession": "ELU_I_80",
                         "institution_name": "INNAXIS Research Institute",
                         "geo_category": "EU",
                         "acronym": "INNAXIS"
                     },
                     {
                         "elu_accession": "ELU_I_81",
                         "institution_name": "SciCross AB",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_82",
                         "institution_name": "University of California -  San Francisco",
                         "geo_category": "Non-EU",
                         "acronym": "UCSF"
                     },
                     {
                         "elu_accession": "ELU_I_83",
                         "institution_name": "The database of Genotypes and Phenotypes",
                         "geo_category": "Non-EU",
                         "acronym": "dbGaP"
                     },
                     {
                         "elu_accession": "ELU_I_84",
                         "institution_name": "Alzheimer's Disease Neuroimaging Initiative",
                         "geo_category": "Non-EU",
                         "acronym": "ADNI"
                     },
                     {
                         "elu_accession": "ELU_I_85",
                         "institution_name": "Parkinson's Progressive Markers Initiative",
                         "geo_category": "Non-EU",
                         "acronym": "PPMI"
                     },
                     {
                         "elu_accession": "ELU_I_86",
                         "institution_name": "Gene Expression Omnibus",
                         "geo_category": "Non-EU",
                         "acronym": "GEO"
                     },
                     {
                         "elu_accession": "ELU_I_87",
                         "institution_name": "Jena University Hospital",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_88",
                         "institution_name": "University Hospital of Geneva",
                         "geo_category": "Non-EU"
                     },
                     {
                         "elu_accession": "ELU_I_89",
                         "institution_name": "Braunschweig University of Technology",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_90",
                         "institution_name": "Hummingbird Diagnostics Heidelberg",
                         "geo_category": "EU"
                     },
                     {
                         "elu_accession": "ELU_I_91",
                         "institution_name": "Helmholtz Zentrum München",
                         "geo_category": "EU",
                         "acronym": "HMGU"
                     },
                     {
                         "elu_accession": "ELU_I_92",
                         "institution_name": "German Cancer Research Center Heidelberg",
                         "geo_category": "EU",
                         "acronym": "DKFZ"
                     },
                     {
                         "elu_accession": "ELU_I_93",
                         "institution_name": "National Cancer Institute",
                         "geo_category": "Non-EU",
                         "acronym": "NCI"
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
