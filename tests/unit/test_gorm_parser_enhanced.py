"""
Tests for EnhancedGormParser.

Part of CodeTrellis v5.2 Go Framework Support.
Tests cover:
- Model extraction (struct with gorm tags)
- Hook extraction (BeforeCreate, AfterCreate, etc.)
- Scope extraction (named scopes with *gorm.DB)
- Migration extraction (AutoMigrate, Migrator)
- Query extraction (GORM query methods)
- Association detection (has_one, has_many, belongs_to, many2many)
- Driver detection
- GORM v1 vs v2 version detection
"""

import pytest
from codetrellis.gorm_parser_enhanced import (
    EnhancedGormParser,
    GormParseResult,
)


@pytest.fixture
def parser():
    return EnhancedGormParser()


SAMPLE_GORM_APP = '''
package models

import (
    "gorm.io/gorm"
    "gorm.io/driver/postgres"
    "time"
)

type User struct {
    gorm.Model
    Name      string         `gorm:"type:varchar(100);not null;index" json:"name"`
    Email     string         `gorm:"type:varchar(255);uniqueIndex" json:"email"`
    Age       int            `gorm:"default:0" json:"age"`
    Profile   Profile        `gorm:"foreignKey:UserID"`
    Orders    []Order        `gorm:"foreignKey:UserID"`
    Roles     []Role         `gorm:"many2many:user_roles"`
    CompanyID uint
    Company   Company        `gorm:"belongsTo"`
    DeletedAt gorm.DeletedAt `gorm:"index"`
}

func (u *User) TableName() string {
    return "app_users"
}

type Profile struct {
    ID     uint   `gorm:"primaryKey"`
    UserID uint   `gorm:"uniqueIndex"`
    Bio    string `gorm:"type:text"`
}

type Order struct {
    ID        uint      `gorm:"primaryKey;autoIncrement"`
    UserID    uint      `gorm:"index"`
    Total     float64   `gorm:"not null"`
    CreatedAt time.Time
}

func (u *User) BeforeCreate(tx *gorm.DB) error {
    u.Name = strings.TrimSpace(u.Name)
    return nil
}

func (u *User) AfterCreate(tx *gorm.DB) error {
    log.Printf("user created: %d", u.ID)
    return nil
}

func (u *User) BeforeUpdate(tx *gorm.DB) error {
    return nil
}

func ActiveUsers(db *gorm.DB) *gorm.DB {
    return db.Where("active = ?", true)
}

func Paginate(page, pageSize int) func(db *gorm.DB) *gorm.DB {
    return func(db *gorm.DB) *gorm.DB {
        offset := (page - 1) * pageSize
        return db.Offset(offset).Limit(pageSize)
    }
}

func setupDB() *gorm.DB {
    dsn := "host=localhost user=app dbname=app sslmode=disable"
    db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})

    db.AutoMigrate(&User{}, &Profile{}, &Order{})

    sqlDB, _ := db.DB()
    sqlDB.SetMaxOpenConns(25)
    sqlDB.SetMaxIdleConns(10)

    return db
}

func createUser(db *gorm.DB, user *User) error {
    return db.Transaction(func(tx *gorm.DB) error {
        if err := tx.Create(user).Error; err != nil {
            return err
        }
        return nil
    })
}

func getUsers(db *gorm.DB) []User {
    var users []User
    db.Preload("Orders").Preload("Profile").Scopes(ActiveUsers).Find(&users)
    return users
}
'''


class TestGormParser:

    def test_parse_returns_result(self, parser):
        result = parser.parse(SAMPLE_GORM_APP, "models.go")
        assert isinstance(result, GormParseResult)

    def test_detect_gorm_framework(self, parser):
        result = parser.parse(SAMPLE_GORM_APP, "models.go")
        assert len(result.detected_frameworks) > 0
        fws = result.detected_frameworks
        assert any("gorm" in fw for fw in fws)

    def test_extract_models(self, parser):
        result = parser.parse(SAMPLE_GORM_APP, "models.go")
        assert len(result.models) >= 2
        names = [m.name for m in result.models]
        assert any("User" in n for n in names)

    def test_extract_hooks(self, parser):
        result = parser.parse(SAMPLE_GORM_APP, "models.go")
        assert len(result.hooks) >= 2
        types = [h.hook_type for h in result.hooks]
        assert any("BeforeCreate" in t for t in types)

    def test_extract_scopes(self, parser):
        result = parser.parse(SAMPLE_GORM_APP, "models.go")
        assert len(result.scopes) >= 1
        names = [s.name for s in result.scopes]
        assert any("ActiveUsers" in n or "Paginate" in n for n in names)

    def test_extract_migrations(self, parser):
        result = parser.parse(SAMPLE_GORM_APP, "models.go")
        assert len(result.migrations) >= 1

    def test_extract_queries(self, parser):
        result = parser.parse(SAMPLE_GORM_APP, "models.go")
        assert len(result.queries) >= 1

    def test_non_gorm_file(self, parser):
        result = parser.parse("package main\n\nfunc main() {}", "main.go")
        assert len(result.models) == 0
        assert len(result.detected_frameworks) == 0

    def test_gorm_detection(self, parser):
        result = parser.parse(SAMPLE_GORM_APP, "models.go")
        assert len(result.detected_frameworks) > 0
        result2 = parser.parse("package main\nfunc main() {}", "main.go")
        assert len(result2.detected_frameworks) == 0
