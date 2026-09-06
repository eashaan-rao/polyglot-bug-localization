"""
Central path configuration for Objective 2 (polyglot bug localization).

Every copied Objective 1 script / src module imports its path constants from
here instead of hardcoding "/home/.../PhD/Objective1/...". This is the single
place to change if the tree moves.

Objective 2 is a fully self-contained copy: repos, embedding DBs and the bug
report parquet all live under PhD/Objective2/data/ (copied for the 6 selected
projects only). Nothing points back into PhD/Objective1/ except the shared
Python virtualenv (obj1/), which is interpreter-only and carries no data.
"""

import os

# Root of the Objective 2 tree (this file is PhD/Objective2/Scripts/paths.py)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

# --- inputs (copied from Objective 1, 6 projects only) ----------------------
REPO_BASE_PATH = os.path.join(DATA_DIR, "repos")
EMBEDDING_DB_DIR = os.path.join(PROCESSED_DIR, "embedding_dbs")
BUG_METADATA_DIR = EMBEDDING_DB_DIR
BLOB_DB_DIR = EMBEDDING_DB_DIR
DATABASE_DIR = EMBEDDING_DB_DIR  # name used by run_faiss_experiment.py
PROJECTS_METADATA_PATH = os.path.join(PROCESSED_DIR, "project_metadata.parquet")
BUG_REPORTS_PATH = os.path.join(PROCESSED_DIR, "bug_reports_clean.parquet")

# GloVe (only needed by COOBA in the CP arm; copied in Phase G)
GLOVE_PATH = os.path.join(DATA_DIR, "glove", "glove.6B.300d.txt")

# --- caches (created on demand, gitignored) --------------------------------
BLAZE_CACHE_DIR = os.path.join(PROCESSED_DIR, "blaze_cache")
BLGAN_CACHE_DIR = os.path.join(PROCESSED_DIR, "blgan_cache")
COOBA_CACHE_DIR = os.path.join(PROCESSED_DIR, "cooba_cache")
TRANP_CNN_CACHE_DIR = os.path.join(PROCESSED_DIR, "tranp_cnn_cache")
FLIM_CACHE_DIR = os.path.join(PROCESSED_DIR, "flim_cache")

# --- outputs --------------------------------------------------------------
RESULT_PATH = os.path.join(RESULTS_DIR, "obj2")

# --- Objective 2 derived artifacts --------------------------------------
OBJ2_DATA_DIR = os.path.join(DATA_DIR, "obj2")
FIX_FILES_RAW_PARQUET = os.path.join(OBJ2_DATA_DIR, "fix_files_raw.parquet")
BUG_CLASSIFICATION_PARQUET = os.path.join(OBJ2_DATA_DIR, "bug_classification.parquet")
BUG_CLASSIFICATION_CSV = os.path.join(RESULT_PATH, "bug_classification.csv")

# --- the 6 selected BeetleBox projects ---------------------------------
SELECTED_PROJECTS = [
    # repo_name (as in bug_reports_clean.parquet / project_metadata.parquet), language
    ("elastic/elasticsearch", "java"),
    ("liquibase/liquibase", "java"),
    ("apache/dolphinscheduler", "java"),
    ("ansible/ansible", "python"),
    ("apache/airflow", "python"),
    ("localstack/localstack", "python"),
]
SELECTED_REPO_NAMES = [r for r, _ in SELECTED_PROJECTS]

for _d in (RESULT_PATH, OBJ2_DATA_DIR):
    os.makedirs(_d, exist_ok=True)
