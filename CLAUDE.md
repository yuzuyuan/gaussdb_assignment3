# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

University database course assignment (Assignment 3): **Community Property Repair & Payment Management System** (社区物业与报修缴费综合管理系统). A desktop C/S application with role-based access, built on GaussDB (PostgreSQL-compatible).

## Tech Stack

- **Language:** Python
- **Database:** GaussDB (PostgreSQL-compatible, use `psycopg2`)
- **GUI:** PyQt6 (hand-written, no Qt Designer)
- **Packaging:** PyInstaller

## Architecture

MVC pattern with strict layer separation:
- **Model** (`db_manager.py`): Database access layer (DAO), connection management, CRUD. No UI or business logic.
- **Controller** (`auth_controller.py`, `main_controller.py`): Business logic, validation, role-based access. No PyQt imports. Returns `{"success": bool, "data": ..., "message": ...}`.
- **View** (`views/`): PyQt6 UI. Login window + main window (left nav + right tab pages). No direct SQL — all actions go through Controller via signals/slots.
- **Entry** (`main.py`): Wires up DB connection, controllers, and views. Launches login window.

## Database

6 core tables: Buildings/Properties, Owners/Residents, Parking Spaces, Property Bills, Repair Orders, Maintenance Staff.

SQL scripts in root:
- `1_schema.sql` — DDL with 3NF/BCNF proof comments, cascading constraints
- `2_advanced_features.sql` — Stored procedures (`sp_generate_monthly_bills`), triggers (`trg_update_staff_workload`)
- `3_init_data.sql` — Views (`v_comprehensive_property_info`), dynamic SQL function (`func_dynamic_search_bills`), test data

Must use parameterized queries (`%s` placeholders) to prevent SQL injection.

## Scoring Requirements

Key features that must be implemented:
- 6+ tables with proper foreign keys and cascading operations (ON DELETE CASCADE/RESTRICT)
- Full CRUD frontend for all tables
- Login with two roles: ADMIN (full access) and OWNER (bills + repair orders only)
- View, dynamic SQL, stored procedure, trigger (database-side features)
- At least 4 distinct PyQt6 components
- Table-level cascade operations in the UI

## Build & Run

```bash
pip install PyQt6 psycopg2-binary
python main.py
```

Package as executable:
```bash
pip install pyinstaller
pyinstaller -w -F --icon=app.ico main.py
```

## Language

All UI text, SQL comments, and documentation are in Chinese (中文).
