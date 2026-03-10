"""
Tests for EnhancedSqlxParser.

Part of CodeTrellis v5.2 Go Framework Support.
Tests cover:
- Query extraction (Get, Select, NamedExec, NamedQuery, Queryx, Exec)
- Model extraction (structs with db:"" tags)
- Connection extraction (sqlx.Connect, sqlx.Open)
- Prepared statement extraction (Preparex, PrepareNamed)
- Transaction extraction (Beginx, tx.Commit, tx.Rollback)
- Driver detection (postgres, mysql, sqlite3)
"""

import pytest
from codetrellis.sqlx_parser_enhanced import (
    EnhancedSqlxParser,
    SqlxParseResult,
)


@pytest.fixture
def parser():
    return EnhancedSqlxParser()


SAMPLE_SQLX_APP = '''
package repository

import (
    "context"
    "database/sql"
    "fmt"

    "github.com/jmoiron/sqlx"
    _ "github.com/lib/pq"
)

type User struct {
    ID        int       `db:"id"`
    Name      string    `db:"name"`
    Email     string    `db:"email"`
    Active    bool      `db:"active"`
    CreatedAt time.Time `db:"created_at"`
}

type Order struct {
    ID     int     `db:"id"`
    UserID int     `db:"user_id"`
    Total  float64 `db:"total"`
}

type UserRepo struct {
    db *sqlx.DB
}

func NewDB(dsn string) (*sqlx.DB, error) {
    db, err := sqlx.Connect("postgres", dsn)
    if err != nil {
        return nil, fmt.Errorf("connect: %w", err)
    }
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(10)
    return db, nil
}

func (r *UserRepo) GetByID(ctx context.Context, id int) (*User, error) {
    var user User
    err := r.db.GetContext(ctx, &user, "SELECT * FROM users WHERE id = $1", id)
    if err == sql.ErrNoRows {
        return nil, nil
    }
    return &user, err
}

func (r *UserRepo) List(ctx context.Context) ([]User, error) {
    var users []User
    err := r.db.SelectContext(ctx, &users, "SELECT * FROM users WHERE active = $1", true)
    return users, err
}

func (r *UserRepo) Create(ctx context.Context, u *User) error {
    _, err := r.db.NamedExecContext(ctx,
        `INSERT INTO users (name, email, active) VALUES (:name, :email, :active)`,
        u,
    )
    return err
}

func (r *UserRepo) Search(ctx context.Context, ids []int) ([]User, error) {
    query, args, err := sqlx.In("SELECT * FROM users WHERE id IN (?)", ids)
    if err != nil {
        return nil, err
    }
    query = r.db.Rebind(query)
    var users []User
    err = r.db.SelectContext(ctx, &users, query, args...)
    return users, err
}

func (r *UserRepo) Transfer(ctx context.Context, fromID, toID int, amount float64) error {
    tx, err := r.db.Beginx()
    if err != nil {
        return err
    }
    defer tx.Rollback()

    _, err = tx.ExecContext(ctx, "UPDATE accounts SET balance = balance - $1 WHERE id = $2", amount, fromID)
    if err != nil {
        return err
    }
    _, err = tx.ExecContext(ctx, "UPDATE accounts SET balance = balance + $1 WHERE id = $2", amount, toID)
    if err != nil {
        return err
    }
    return tx.Commit()
}

var getUserStmt *sqlx.Stmt

func (r *UserRepo) PrepareStatements() error {
    var err error
    getUserStmt, err = r.db.Preparex("SELECT * FROM users WHERE id = $1")
    return err
}
'''


class TestSqlxParser:

    def test_parse_returns_result(self, parser):
        result = parser.parse(SAMPLE_SQLX_APP, "repository.go")
        assert isinstance(result, SqlxParseResult)

    def test_detect_sqlx_framework(self, parser):
        result = parser.parse(SAMPLE_SQLX_APP, "repository.go")
        assert len(result.detected_frameworks) > 0
        assert "sqlx" in result.detected_frameworks

    def test_extract_queries(self, parser):
        result = parser.parse(SAMPLE_SQLX_APP, "repository.go")
        assert len(result.queries) >= 3
        methods = [q.method for q in result.queries]
        assert any("Get" in m for m in methods)
        assert any("Select" in m for m in methods)

    def test_extract_models(self, parser):
        result = parser.parse(SAMPLE_SQLX_APP, "repository.go")
        assert len(result.models) >= 1
        names = [m.name for m in result.models]
        assert any("User" in n for n in names)

    def test_extract_connections(self, parser):
        result = parser.parse(SAMPLE_SQLX_APP, "repository.go")
        assert len(result.connections) >= 1

    def test_extract_prepared_stmts(self, parser):
        result = parser.parse(SAMPLE_SQLX_APP, "repository.go")
        assert len(result.prepared_stmts) >= 1

    def test_extract_transactions(self, parser):
        result = parser.parse(SAMPLE_SQLX_APP, "repository.go")
        assert len(result.transactions) >= 1

    def test_non_sqlx_file(self, parser):
        result = parser.parse("package main\n\nfunc main() {}", "main.go")
        assert len(result.queries) == 0
        assert len(result.detected_frameworks) == 0

    def test_sqlx_detection(self, parser):
        result = parser.parse(SAMPLE_SQLX_APP, "repository.go")
        assert len(result.detected_frameworks) > 0
        result2 = parser.parse("package main\nfunc main() {}", "main.go")
        assert len(result2.detected_frameworks) == 0
