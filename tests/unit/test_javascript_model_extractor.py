"""
Tests for JavaScriptModelExtractor — model, migration, relationship extraction.

Part of CodeTrellis v4.30 JavaScript Language Support.
"""

import pytest
from codetrellis.extractors.javascript.model_extractor import (
    JavaScriptModelExtractor,
    JSModelInfo,
    JSSchemaFieldInfo,
    JSMigrationInfo,
    JSRelationInfo,
)


@pytest.fixture
def extractor():
    return JavaScriptModelExtractor()


class TestMongooseModels:
    """Tests for Mongoose model extraction."""

    def test_basic_schema(self, extractor):
        code = '''
const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
    name: { type: String, required: true },
    email: { type: String, unique: true },
    age: Number,
    role: { type: String, enum: ['admin', 'user'], default: 'user' },
});

const User = mongoose.model('User', userSchema);
module.exports = User;
'''
        result = extractor.extract(code, "user.model.js")
        models = result.get('models', [])
        assert len(models) >= 1
        model = models[0]
        assert model.name == "User"
        assert model.orm == "mongoose"

    def test_schema_with_refs(self, extractor):
        code = '''
const postSchema = new mongoose.Schema({
    title: String,
    body: String,
    author: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    comments: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Comment' }],
});

const Post = mongoose.model('Post', postSchema);
'''
        result = extractor.extract(code, "post.model.js")
        models = result.get('models', [])
        assert len(models) >= 1

    def test_schema_with_hooks(self, extractor):
        code = '''
const userSchema = new mongoose.Schema({
    password: String,
});

userSchema.pre('save', async function(next) {
    this.password = await bcrypt.hash(this.password, 10);
    next();
});

userSchema.post('save', function(doc) {
    console.log('Saved:', doc._id);
});

const User = mongoose.model('User', userSchema);
'''
        result = extractor.extract(code, "user_hooks.js")
        models = result.get('models', [])
        assert len(models) >= 1


class TestSequelizeModels:
    """Tests for Sequelize model extraction."""

    def test_sequelize_define(self, extractor):
        code = '''
const { DataTypes } = require('sequelize');

const Product = sequelize.define('Product', {
    name: {
        type: DataTypes.STRING,
        allowNull: false,
    },
    price: {
        type: DataTypes.DECIMAL(10, 2),
        allowNull: false,
    },
    sku: {
        type: DataTypes.STRING,
        unique: true,
    },
});

module.exports = Product;
'''
        result = extractor.extract(code, "product.model.js")
        models = result.get('models', [])
        assert len(models) >= 1
        assert models[0].orm == "sequelize"

    def test_sequelize_associations(self, extractor):
        code = '''
const User = sequelize.define('User', {
    name: DataTypes.STRING,
});

User.hasMany(Post);
User.belongsToMany(Role, { through: 'UserRoles' });
'''
        result = extractor.extract(code, "associations.js")
        relationships = result.get('relationships', [])
        assert len(relationships) >= 1


class TestMigrations:
    """Tests for migration extraction."""

    def test_knex_migration(self, extractor):
        code = '''
exports.up = function(knex) {
    return knex.schema.createTable('users', (table) => {
        table.increments('id');
        table.string('name').notNullable();
        table.string('email').unique();
        table.timestamps(true, true);
    });
};

exports.down = function(knex) {
    return knex.schema.dropTable('users');
};
'''
        result = extractor.extract(code, "20230101_create_users.js")
        migrations = result.get('migrations', [])
        assert len(migrations) >= 1

    def test_sequelize_migration(self, extractor):
        code = '''
module.exports = {
    up: async (queryInterface, Sequelize) => {
        await queryInterface.createTable('orders', {
            id: {
                type: Sequelize.INTEGER,
                primaryKey: true,
                autoIncrement: true,
            },
            total: Sequelize.DECIMAL,
        });
    },
    down: async (queryInterface) => {
        await queryInterface.dropTable('orders');
    },
};
'''
        result = extractor.extract(code, "migration.js")
        migrations = result.get('migrations', [])
        assert len(migrations) >= 1


class TestRelationships:
    """Tests for relationship extraction."""

    def test_mongoose_populate(self, extractor):
        code = '''
const orderSchema = new mongoose.Schema({
    customer: { type: mongoose.Schema.Types.ObjectId, ref: 'Customer' },
    items: [{ type: mongoose.Schema.Types.ObjectId, ref: 'Product' }],
});

const Order = mongoose.model('Order', orderSchema);
'''
        result = extractor.extract(code, "order.js")
        models = result.get('models', [])
        assert len(models) >= 1

    def test_sequelize_belongs_to(self, extractor):
        code = '''
const Comment = sequelize.define('Comment', {
    text: DataTypes.TEXT,
});

Comment.belongsTo(User);
Comment.belongsTo(Post);
'''
        result = extractor.extract(code, "comment.js")
        relationships = result.get('relationships', [])
        assert len(relationships) >= 1
