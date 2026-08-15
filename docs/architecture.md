# NovusFi Platform Architecture

## Overview
The NovusFi data platform is built on Databricks using a modern Medallion Architecture (Bronze, Silver, Gold). To maximize engineering efficiency and accessibility, we employ a hybrid processing model: **PySpark** handles data extraction and early-stage processing, while **dbt (Data Build Tool)** manages downstream analytical modeling.

## Core Design Principles
* **Domain-Driven Design:** Code is organized by business domain (e.g., `exchange_rates`, `loan_collections`, `payment_gateway`) rather than technical function to ensure scalability.
* **Idempotency:** All pipelines are designed to be re-runnable without causing data duplication.
* **Separation of Concerns:** Python is used for interacting with external systems and handling messy JSON/API data. SQL is used for aggregations, business logic, and dimensional modeling.
* **Event Sourcing (Immutable Ledgers):** The platform calculates loan states (e.g., Active, Paid Off, Default) dynamically in the Gold layer using raw operational events (Originations + Payments), establishing the Data Lakehouse as a governed engine for business logic.

## Architecture Decisions & Trade-offs
* **Reconciliation vs. Event Sourcing:** In a full enterprise production environment, calculating financial state downstream can introduce "data drift" from the core operational database (System of Record). A real-world deployment of this architecture would include a **Systematic Reconciliation** step: ingesting a daily End-of-Day (EOD) Trial Balance snapshot from the core system to run Data Quality alerts against the Gold layer's calculated balances. For the scope of this portfolio project, the EOD reconciliation pipeline is omitted to focus purely on event-driven PySpark and dbt transformations.

## The Medallion Layers

### 1. Bronze (Raw Data)
* **Tooling:** Databricks / PySpark
* **Location:** `src/pipelines/{domain}/`
* **Purpose:** Acts as a historical archive. Data is ingested from external APIs, databases, and **Databricks Unity Catalog Volumes** (simulating S3/ADLS file drops) as raw JSON, CSV, or Parquet files. No transformations are applied here other than appending load metadata (e.g., `_ingest_timestamp`).

### 2. Silver (Cleaned & Conformed)
* **Tooling:** Databricks / PySpark
* **Location:** `src/pipelines/{domain}/`
* **Purpose:** Data is unnested, deduplicated, and cast to strict schemas. Column names are standardized to snake_case. This layer provides a "single source of truth" for the raw operational data.

### 3. Gold (Business Level & Presentation)
* **Tooling:** dbt (SQL)
* **Location:** `dbt_novusfi/models/`
* **Purpose:** Highly polished, aggregated data designed directly for BI tools and business users. 
    * **Staging:** 1-to-1 pointers to Silver tables.
    * **Intermediate:** Complex joins and metrics calculation.
    * **Marts:** Final dimensional models (Star Schema) divided by enterprise domain (Core, Collections, Originations).

## Repository Structure
This repository uses a monorepo approach to store both infrastructure configurations (Databricks Asset Bundles) and data transformation code (Python/SQL).

```text
novusfi-platform/
│
├── .github/                            
│   └── workflows/
│       ├── pr_tests.yml                 # Lint + unit + dbt tests on every PR
│       └── deploy_databricks.yml        # DAB deploy to prod on merge to main
│
├── docs/                                
│   ├── architecture.md                  # Why PySpark for Bronze/Silver, dbt for Gold
│   └── architecture_diagram.mmd         # Mermaid: sources → bronze → silver → gold → BI
│
├── conf/                                
│   ├── dev_config.yaml                  # Dev database paths, small cluster sizes
│   └── prod_config.yaml                 # Prod database paths, large cluster sizes
│
├── .env.example                         # SHOWS SECURITY: strategies without exposing secrets
│
├── infrastructure/                      
│   ├── databricks.yml                   # DAB definition, references secret scopes
│   └── resources/
│       ├── job_exchange_rates.yml       # Schedules the PySpark extraction job
│       ├── job_loan_collections.yml     # Schedules the downstream dbt transformations
│       └── job_payment_gateway.yml      # Schedules the payment CSV ingestion
│
├── src/                                 # THE PYTHON / PYSPARK ENGINE (Extraction & Silver)
│   ├── pipelines/
│   │   ├── exchange_rates/              # Pipeline 1: FX API 
│   │   │   ├── 01_extract_exchange_rates.py         # Extracts live data from external REST API    
│   │   │   ├── 02_ingest_exchange_rates_bronze.py     
│   │   │   └── 03_transform_exchange_rates_silver.py  
│   │   │
│   │   ├── loan_collections/            # Pipeline 2: Credit Risk & Microloans 
│   │   │   ├── 01_ingest_loans_bronze.py     
│   │   │   └── 02_transform_loans_silver.py  
│   │   │
│   │   └── payment_gateway/             # Pipeline 3: Daily CSV Drop via UC Volumes
│   │       ├── 01_ingest_payments_bronze.py     
│   │       └── 02_transform_payments_silver.py  
│   │
│   ├── data_generator/                  
│   │   ├── generate_loan_records.py     # Synthetic loan/collections records
│   │   └── generate_payment_records.py  # Simulates daily Stripe/Gateway CSV drop
│   │
│   └── shared_utils/
│       ├── spark_session.py            
│       ├── schema_registry.py          
│       ├── secrets.py                   # Wraps Databricks secret scope calls
│       └── custom_logger.py            
│
├── tests/                               
│   ├── unit/
│   │   ├── test_exchange_rates.py      
│   │   ├── test_loan_collections.py    
│   │   └── test_payment_gateway.py      # Unit tests for payment processing
│   └── integration/
│       └── test_silver_layer.py        
│
├── dbt_novusfi/                         # THE DBT ENGINE (SQL) - Domain-Driven Design 
│   ├── models/
│   │   ├── staging/                     # 1-to-1 pointers to Python's Silver layer
│   │   │   ├── exchange_rates/         
│   │   │   │   ├── src_finance.yml    
│   │   │   │   ├── stg_exchange_rates.sql
│   │   │   │   └── schema.yml          
│   │   │   ├── loan_system/
│   │   │   │   ├── src_loans.yml       
│   │   │   │   ├── stg_loan_collections.sql
│   │   │   │   └── schema.yml          
│   │   │   └── payment_gateway/         # Staging for new Payments pipeline
│   │   │       ├── src_payments.yml       
│   │   │       ├── stg_payments.sql
│   │   │       └── schema.yml          
│   │   │
│   │   ├── intermediate/                # THE PREP KITCHEN: Where complex logic lives
│   │   │   └── finance/
│   │   │       ├── int_payments_currency_adjusted.sql
│   │   │       └── schema.yml          
│   │   │
│   │   └── marts/                       # THE GOLD LAYER: Isolated by domain!
│   │       ├── core/                    # Shared enterprise dimensions
│   │       │   ├── dim_currency.sql    
│   │       │   ├── dim_date.sql        
│   │       │   └── schema.yml          
│   │       │
│   │       ├── collections/             
│   │       │   ├── dim_borrower.sql    
│   │       │   ├── fct_collections_daily.sql
│   │       │   └── schema.yml          
│   │       │
│   │       └── originations/            
│   │           ├── fct_new_loans.sql   
│   │           └── schema.yml          
│   │
│   ├── seeds/                           
│   │   └── currency_lookup.csv          # Static reference data
│   ├── macros/                          
│   │   └── convert_currency.sql         # DRY custom SQL functions
│   ├── snapshots/                       
│   │   └── loan_status_history.sql      # SCD Type 2 tracking
│   ├── packages.yml                     # dbt_utils dependency
│   └── dbt_project.yml                 
│
├── Makefile                            
├── pyproject.toml                      
├── .pre-commit-config.yaml             
├── .gitignore                          
└── README.md                            # Now includes an "Architecture Decisions" section