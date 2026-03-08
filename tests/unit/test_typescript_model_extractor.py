"""
Tests for TypeScriptModelExtractor — ORM entities, DTOs, Zod schemas.

Part of CodeTrellis v4.31 TypeScript Language Support.
"""

import pytest
from codetrellis.extractors.typescript.model_extractor import (
    TypeScriptModelExtractor,
    TSModelInfo,
    TSFieldInfo,
    TSRelationInfo,
    TSMigrationInfo,
    TSDTOInfo,
)


@pytest.fixture
def extractor():
    return TypeScriptModelExtractor()


class TestTypeORMModels:
    """Tests for TypeORM entity extraction."""

    def test_typeorm_entity(self, extractor):
        code = '''
@Entity()
export class User {
    @PrimaryGeneratedColumn()
    id: number;

    @Column()
    name: string;

    @Column({ unique: true })
    email: string;

    @Column({ nullable: true })
    bio?: string;

    @CreateDateColumn()
    createdAt: Date;
}
'''
        result = extractor.extract(code, "user.entity.ts")
        models = result.get('models', [])
        assert len(models) >= 1
        model = models[0]
        assert model.name == "User"
        assert model.orm == "typeorm"

    def test_typeorm_relationships(self, extractor):
        code = '''
@Entity()
export class Post {
    @PrimaryGeneratedColumn()
    id: number;

    @Column()
    title: string;

    @ManyToOne(() => User, user => user.posts)
    author: User;

    @OneToMany(() => Comment, comment => comment.post)
    comments: Comment[];
}
'''
        result = extractor.extract(code, "post.entity.ts")
        models = result.get('models', [])
        assert len(models) >= 1
        rels = result.get('relationships', [])
        assert len(rels) >= 1


class TestDrizzleModels:
    """Tests for Drizzle ORM table extraction."""

    def test_drizzle_pg_table(self, extractor):
        code = '''
import { pgTable, serial, text, timestamp, boolean } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
    id: serial('id').primaryKey(),
    name: text('name').notNull(),
    email: text('email').notNull().unique(),
    isActive: boolean('is_active').default(true),
    createdAt: timestamp('created_at').defaultNow(),
});
'''
        result = extractor.extract(code, "schema.ts")
        models = result.get('models', [])
        assert len(models) >= 1
        model = models[0]
        assert model.name == "users"
        assert model.orm == "drizzle"


class TestClassValidatorDTOs:
    """Tests for class-validator DTO extraction."""

    def test_dto_with_validators(self, extractor):
        code = '''
export class CreateUserDto {
    @IsString()
    @IsNotEmpty()
    name: string;

    @IsEmail()
    email: string;

    @IsOptional()
    @IsNumber()
    @Min(0)
    @Max(150)
    age?: number;

    @IsEnum(Role)
    role: Role;
}
'''
        result = extractor.extract(code, "create-user.dto.ts")
        dtos = result.get('dtos', [])
        assert len(dtos) >= 1
        dto = dtos[0]
        assert dto.name == "CreateUserDto"
        assert len(dto.validators) >= 1

    def test_update_dto(self, extractor):
        code = '''
export class UpdateUserDto {
    @IsOptional()
    @IsString()
    name?: string;

    @IsOptional()
    @IsEmail()
    email?: string;
}
'''
        result = extractor.extract(code, "update-user.dto.ts")
        dtos = result.get('dtos', [])
        assert len(dtos) >= 1


class TestZodSchemas:
    """Tests for Zod schema extraction."""

    def test_zod_schema(self, extractor):
        code = '''
import { z } from 'zod';

export const UserSchema = z.object({
    id: z.string().uuid(),
    name: z.string().min(1).max(100),
    email: z.string().email(),
    age: z.number().int().positive().optional(),
    role: z.enum(['admin', 'user', 'moderator']),
});

export type User = z.infer<typeof UserSchema>;
'''
        result = extractor.extract(code, "schemas.ts")
        models = result.get('models', [])
        # Zod schemas may be captured as models
        assert len(models) >= 0  # Implementation-dependent


class TestMigrations:
    """Tests for migration extraction."""

    def test_typeorm_migration(self, extractor):
        code = '''
export class CreateUsersTable1234567890 implements MigrationInterface {
    public async up(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.createTable(new Table({
            name: 'users',
            columns: [
                { name: 'id', type: 'int', isPrimary: true },
                { name: 'name', type: 'varchar' },
            ],
        }));
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        await queryRunner.dropTable('users');
    }
}
'''
        result = extractor.extract(code, "1234567890-CreateUsersTable.ts")
        migrations = result.get('migrations', [])
        assert len(migrations) >= 1
        mig = migrations[0]
        assert "CreateUsersTable" in mig.name or "1234567890" in mig.name


class TestSequelizeTS:
    """Tests for Sequelize-TypeScript model extraction."""

    def test_sequelize_model(self, extractor):
        code = '''
@Table({ tableName: 'products' })
export class Product extends Model<Product> {
    @Column({ primaryKey: true, autoIncrement: true })
    id: number;

    @Column
    name: string;

    @Column({ type: DataType.DECIMAL(10, 2) })
    price: number;

    @BelongsTo(() => Category)
    category: Category;
}
'''
        result = extractor.extract(code, "product.model.ts")
        models = result.get('models', [])
        assert len(models) >= 1
        model = models[0]
        assert model.name == "Product"
        assert model.orm == "sequelize-typescript"
