"""Job B: weekly incremental ETL.

Discovers newly completed NRL matches, scrapes raw JSON into the shared data
lake, full-rebuilds the feature store, and retrains the production model.
"""
