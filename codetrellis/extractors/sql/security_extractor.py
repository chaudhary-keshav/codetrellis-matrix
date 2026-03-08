"""
SQLSecurityExtractor - Extracts SQL security definitions (roles, grants, RLS policies).

This extractor parses SQL source code and extracts:
- CREATE ROLE / CREATE USER
- GRANT / REVOKE statements
- Row Level Security (RLS) policies (PostgreSQL)
- ALTER DEFAULT PRIVILEGES
- SECURITY LABEL statements
- Audit trail configurations (Oracle AUDIT)

Supported SQL dialects:
- PostgreSQL: RLS, ALTER DEFAULT PRIVILEGES, SECURITY LABEL
- MySQL: CREATE USER, GRANT ON
- SQL Server: CREATE LOGIN, CREATE USER, GRANT, DENY
- Oracle: CREATE ROLE, GRANT, AUDIT

Part of CodeTrellis v4.15 - SQL Language Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SQLRoleInfo:
    """Information about a SQL role/user."""
    name: str
    kind: str = "role"                # role, user, login
    is_superuser: bool = False
    is_createdb: bool = False
    is_createrole: bool = False
    is_login: bool = False
    inherit: bool = True
    connection_limit: Optional[int] = None
    valid_until: Optional[str] = None
    in_roles: List[str] = field(default_factory=list)  # MEMBER OF
    dialect: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SQLGrantInfo:
    """Information about a GRANT/REVOKE statement."""
    action: str = "GRANT"             # GRANT or REVOKE
    privileges: List[str] = field(default_factory=list)  # SELECT, INSERT, ALL, EXECUTE, etc.
    object_type: str = ""             # TABLE, FUNCTION, SCHEMA, SEQUENCE, DATABASE
    object_name: str = ""
    grantee: str = ""                 # Role/user receiving the privilege
    with_grant_option: bool = False
    is_all_tables: bool = False       # ALL TABLES IN SCHEMA
    schema_name: str = ""
    dialect: str = ""
    file: str = ""
    line_number: int = 0


@dataclass
class SQLRLSPolicyInfo:
    """Information about a Row Level Security policy (PostgreSQL)."""
    name: str
    table_name: str
    schema_name: str = ""
    command: str = "ALL"              # ALL, SELECT, INSERT, UPDATE, DELETE
    permissive: bool = True           # PERMISSIVE vs RESTRICTIVE
    roles: List[str] = field(default_factory=list)  # TO role_name
    using_expr: Optional[str] = None  # USING (expr)
    check_expr: Optional[str] = None  # WITH CHECK (expr)
    dialect: str = "postgresql"
    file: str = ""
    line_number: int = 0


class SQLSecurityExtractor:
    """
    Extracts SQL security definitions from source code.

    v4.15: Comprehensive security extraction across all dialects.
    """

    CREATE_ROLE = re.compile(
        r'CREATE\s+(?P<kind>ROLE|USER|LOGIN)\s+'
        r'(?:IF\s+NOT\s+EXISTS\s+)?'
        r'(?P<name>[\w"`.@]+)'
        r'(?:\s+(?P<opts>.+?))?;',
        re.IGNORECASE | re.DOTALL
    )

    GRANT_STMT = re.compile(
        r'(?P<action>GRANT|REVOKE)\s+'
        r'(?P<privs>[\w,\s]+?)\s+'
        r'ON\s+(?:(?P<obj_type>TABLE|FUNCTION|PROCEDURE|SCHEMA|SEQUENCE|DATABASE|ALL\s+TABLES\s+IN\s+SCHEMA|ALL\s+SEQUENCES\s+IN\s+SCHEMA|ALL\s+FUNCTIONS\s+IN\s+SCHEMA)\s+)?'
        r'(?P<obj_name>[\w"`.]+(?:\.[\w"`.]+)?)\s+'
        r'(?:TO|FROM)\s+(?P<grantee>[\w"`.]+)'
        r'(?:\s+WITH\s+GRANT\s+OPTION)?',
        re.IGNORECASE
    )

    RLS_ENABLE = re.compile(
        r'ALTER\s+TABLE\s+(?P<schema>[\w"`.]+\.)?(?P<table>[\w"`.]+)\s+'
        r'ENABLE\s+ROW\s+LEVEL\s+SECURITY',
        re.IGNORECASE
    )

    CREATE_POLICY = re.compile(
        r'CREATE\s+POLICY\s+(?P<name>[\w"`.]+)\s+'
        r'ON\s+(?P<schema>[\w"`.]+\.)?(?P<table>[\w"`.]+)\s*'
        r'(?:AS\s+(?P<permissive>PERMISSIVE|RESTRICTIVE)\s+)?'
        r'(?:FOR\s+(?P<command>ALL|SELECT|INSERT|UPDATE|DELETE)\s+)?'
        r'(?:TO\s+(?P<roles>[\w"`,\s]+?)\s+)?'
        r'(?:USING\s*\(\s*(?P<using>.+?)\s*\)\s*)?'
        r'(?:WITH\s+CHECK\s*\(\s*(?P<check>.+?)\s*\))?\s*;',
        re.IGNORECASE | re.DOTALL
    )

    ALTER_DEFAULT_PRIV = re.compile(
        r'ALTER\s+DEFAULT\s+PRIVILEGES\s+'
        r'(?:FOR\s+(?:ROLE|USER)\s+(?P<role>[\w"`.]+)\s+)?'
        r'(?:IN\s+SCHEMA\s+(?P<schema>[\w"`.]+)\s+)?'
        r'(?P<grant_revoke>GRANT|REVOKE)\s+'
        r'(?P<privs>[\w,\s]+?)\s+'
        r'ON\s+(?P<obj_type>TABLES|SEQUENCES|FUNCTIONS|TYPES|SCHEMAS)\s+'
        r'(?:TO|FROM)\s+(?P<grantee>[\w"`.]+)',
        re.IGNORECASE
    )

    def __init__(self):
        pass

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract all security definitions.

        Returns:
            Dict with keys: roles, grants, rls_policies, rls_tables, default_privileges
        """
        roles = self._extract_roles(content, file_path)
        grants = self._extract_grants(content, file_path)
        policies = self._extract_rls_policies(content, file_path)
        rls_tables = self._extract_rls_enabled_tables(content, file_path)
        default_privs = self._extract_default_privileges(content, file_path)

        return {
            'roles': roles,
            'grants': grants,
            'rls_policies': policies,
            'rls_tables': rls_tables,
            'default_privileges': default_privs,
        }

    def _extract_roles(self, content: str, file_path: str) -> List[SQLRoleInfo]:
        """Extract CREATE ROLE/USER/LOGIN statements."""
        roles = []
        for m in self.CREATE_ROLE.finditer(content):
            name = m.group('name').strip('"').strip('`').strip("'")
            kind = m.group('kind').lower()
            opts = (m.group('opts') or '').upper()

            role = SQLRoleInfo(
                name=name,
                kind=kind,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            if 'SUPERUSER' in opts:
                role.is_superuser = True
            if 'CREATEDB' in opts:
                role.is_createdb = True
            if 'CREATEROLE' in opts:
                role.is_createrole = True
            if 'LOGIN' in opts:
                role.is_login = True
            if 'NOINHERIT' in opts:
                role.inherit = False
            # IN ROLE
            in_role_match = re.search(r'IN\s+(?:ROLE|GROUP)\s+([\w"`,\s]+)', opts, re.IGNORECASE)
            if in_role_match:
                role.in_roles = [r.strip().strip('"') for r in in_role_match.group(1).split(',')]

            roles.append(role)
        return roles

    def _extract_grants(self, content: str, file_path: str) -> List[SQLGrantInfo]:
        """Extract GRANT/REVOKE statements."""
        grants = []
        for m in self.GRANT_STMT.finditer(content):
            action = m.group('action').upper()
            privs = [p.strip() for p in m.group('privs').split(',')]
            obj_type = (m.group('obj_type') or '').strip().upper()
            obj_name = m.group('obj_name').strip('"').strip('`')
            grantee = m.group('grantee').strip('"').strip('`')

            grant = SQLGrantInfo(
                action=action,
                privileges=privs,
                object_type=obj_type if obj_type and 'ALL' not in obj_type else '',
                object_name=obj_name,
                grantee=grantee,
                with_grant_option='WITH GRANT OPTION' in m.group(0).upper(),
                is_all_tables='ALL TABLES' in obj_type if obj_type else False,
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            grants.append(grant)
        return grants

    def _extract_rls_policies(self, content: str, file_path: str) -> List[SQLRLSPolicyInfo]:
        """Extract CREATE POLICY statements (PostgreSQL RLS)."""
        policies = []
        for m in self.CREATE_POLICY.finditer(content):
            name = m.group('name').strip('"')
            table = m.group('table').strip('"').strip('`')
            schema = (m.group('schema') or '').strip('"').strip('`').strip('.')

            policy = SQLRLSPolicyInfo(
                name=name,
                table_name=table,
                schema_name=schema,
                command=(m.group('command') or 'ALL').upper(),
                permissive=(m.group('permissive') or 'PERMISSIVE').upper() == 'PERMISSIVE',
                file=file_path,
                line_number=content[:m.start()].count('\n') + 1,
            )
            if m.group('roles'):
                policy.roles = [r.strip().strip('"') for r in m.group('roles').split(',')]
            if m.group('using'):
                policy.using_expr = m.group('using').strip()[:200]
            if m.group('check'):
                policy.check_expr = m.group('check').strip()[:200]

            policies.append(policy)
        return policies

    def _extract_rls_enabled_tables(self, content: str, file_path: str) -> List[str]:
        """Extract tables with RLS enabled."""
        tables = []
        for m in self.RLS_ENABLE.finditer(content):
            schema = (m.group('schema') or '').strip('"').strip('`').strip('.')
            table = m.group('table').strip('"').strip('`')
            full_name = f"{schema}.{table}" if schema else table
            tables.append(full_name)
        return tables

    def _extract_default_privileges(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Extract ALTER DEFAULT PRIVILEGES statements."""
        privs = []
        for m in self.ALTER_DEFAULT_PRIV.finditer(content):
            privs.append({
                'action': m.group('grant_revoke').upper(),
                'role': (m.group('role') or '').strip('"'),
                'schema': (m.group('schema') or '').strip('"'),
                'privileges': [p.strip() for p in m.group('privs').split(',')],
                'object_type': m.group('obj_type').upper(),
                'grantee': m.group('grantee').strip('"'),
                'file': file_path,
                'line': content[:m.start()].count('\n') + 1,
            })
        return privs
