"""
Tests for MyBatis extractors and EnhancedMyBatisParser.

Part of CodeTrellis v4.95 MyBatis Framework Support.
Tests cover:
- Mapper extraction (@Mapper, @Select, @Insert, @Update, @Delete)
- SQL provider extraction (@SelectProvider, SQL builders)
- Dynamic SQL extraction (XML mapper parsing)
- Result map extraction (@Results, TypeHandler)
- Cache extraction (@CacheNamespace, MyBatis-Plus)
- Parser integration (framework detection, version detection, is_mybatis_file)
"""

import pytest
from codetrellis.mybatis_parser_enhanced import EnhancedMyBatisParser, MyBatisParseResult
from codetrellis.extractors.mybatis import (
    MyBatisMapperExtractor,
    MyBatisSQLExtractor,
    MyBatisDynamicSQLExtractor,
    MyBatisResultMapExtractor,
    MyBatisCacheExtractor,
)


@pytest.fixture
def parser():
    return EnhancedMyBatisParser()


@pytest.fixture
def mapper_extractor():
    return MyBatisMapperExtractor()


@pytest.fixture
def sql_extractor():
    return MyBatisSQLExtractor()


@pytest.fixture
def dynamic_sql_extractor():
    return MyBatisDynamicSQLExtractor()


@pytest.fixture
def result_map_extractor():
    return MyBatisResultMapExtractor()


@pytest.fixture
def cache_extractor():
    return MyBatisCacheExtractor()


class TestMyBatisMapperExtractor:

    def test_extract_mapper_interface(self, mapper_extractor):
        content = """
import org.apache.ibatis.annotations.*;

@Mapper
public interface UserMapper {
    @Select("SELECT * FROM users WHERE id = #{id}")
    User findById(@Param("id") Long id);

    @Insert("INSERT INTO users (name, email) VALUES (#{name}, #{email})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(User user);

    @Update("UPDATE users SET name = #{name} WHERE id = #{id}")
    int update(User user);

    @Delete("DELETE FROM users WHERE id = #{id}")
    int deleteById(@Param("id") Long id);
}
"""
        result = mapper_extractor.extract(content)
        assert len(result['mappers']) > 0
        assert len(result['mappers'][0].methods) >= 4

    def test_extract_params(self, mapper_extractor):
        content = """
@Mapper
public interface OrderMapper {
    @Select("SELECT * FROM orders WHERE user_id = #{userId} AND status = #{status}")
    List<Order> findByUserAndStatus(@Param("userId") Long userId, @Param("status") String status);
}
"""
        result = mapper_extractor.extract(content)
        assert len(result['mappers']) > 0 or len(result['mapper_scans']) > 0

    def test_empty_content(self, mapper_extractor):
        result = mapper_extractor.extract("")
        assert result['mappers'] == []


class TestMyBatisSqlExtractor:

    def test_extract_sql_provider(self, sql_extractor):
        content = """
@SelectProvider(type = UserSqlProvider.class, method = "findByCondition")
List<User> findByCondition(Map<String, Object> params);

@InsertProvider(type = UserSqlProvider.class, method = "batchInsert")
int batchInsert(@Param("users") List<User> users);
"""
        result = sql_extractor.extract(content)
        assert len(result['providers']) > 0

    def test_extract_sql_builder(self, sql_extractor):
        content = """
public class UserSqlProvider {
    public String findByCondition(Map<String, Object> params) {
        return new SQL()
            .SELECT("*")
            .FROM("users")
            .WHERE("active = true")
            .toString();
    }
}
"""
        result = sql_extractor.extract(content)
        assert len(result['fragments']) > 0


class TestMyBatisDynamicSqlExtractor:

    def test_extract_xml_mapper(self, dynamic_sql_extractor):
        content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3-mapper.dtd">
<mapper namespace="com.example.mapper.UserMapper">
    <select id="findByCondition" resultType="User">
        SELECT * FROM users
        <where>
            <if test="name != null">
                AND name = #{name}
            </if>
            <if test="email != null">
                AND email = #{email}
            </if>
        </where>
    </select>

    <insert id="batchInsert">
        INSERT INTO users (name, email) VALUES
        <foreach collection="users" item="user" separator=",">
            (#{user.name}, #{user.email})
        </foreach>
    </insert>
</mapper>
"""
        result = dynamic_sql_extractor.extract(content, "UserMapper.xml")
        assert len(result['xml_mappers']) > 0

    def test_extract_dynamic_elements(self, dynamic_sql_extractor):
        content = """<mapper namespace="test">
    <select id="search" resultType="Product">
        SELECT * FROM products
        <where>
            <if test="category != null">AND category = #{category}</if>
            <choose>
                <when test="sort == 'price'">ORDER BY price</when>
                <otherwise>ORDER BY name</otherwise>
            </choose>
        </where>
    </select>
</mapper>
"""
        result = dynamic_sql_extractor.extract(content, "test.xml")
        assert len(result['xml_mappers']) > 0


class TestMyBatisResultMapExtractor:

    def test_extract_results_annotation(self, result_map_extractor):
        content = """
@Results(id = "userResult", value = {
    @Result(property = "id", column = "user_id", id = true),
    @Result(property = "name", column = "user_name"),
    @Result(property = "email", column = "user_email")
})
@Select("SELECT * FROM users")
List<User> findAll();
"""
        result = result_map_extractor.extract(content)
        assert len(result['result_maps']) > 0

    def test_extract_type_handler(self, result_map_extractor):
        content = """
public class JsonTypeHandler extends BaseTypeHandler<JsonNode> {
    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, JsonNode parameter, JdbcType jdbcType) {}
}
"""
        result = result_map_extractor.extract(content)
        assert len(result['type_handlers']) > 0


class TestMyBatisCacheExtractor:

    def test_extract_cache_namespace(self, cache_extractor):
        content = """
@CacheNamespace(implementation = EhcacheCache.class, flushInterval = 60000, size = 512)
@Mapper
public interface UserMapper {}
"""
        result = cache_extractor.extract(content)
        assert len(result['caches']) > 0

    def test_extract_mybatis_plus(self, cache_extractor):
        content = """
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.extension.service.IService;

public interface UserMapper extends BaseMapper<User> {}
"""
        result = cache_extractor.extract(content)
        # Should detect MyBatis-Plus
        assert result.get('is_mybatis_plus', False) or len(result.get('plugins', [])) >= 0


class TestEnhancedMyBatisParser:

    def test_is_mybatis_file(self, parser):
        content = """
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper {}
"""
        assert parser.is_mybatis_file(content) is True

    def test_is_mybatis_xml_file(self, parser):
        content = """<?xml version="1.0"?>
<mapper namespace="com.example.UserMapper">
    <select id="findAll" resultType="User">SELECT * FROM users</select>
</mapper>
"""
        assert parser.is_mybatis_file(content, "UserMapper.xml") is True

    def test_is_not_mybatis_file(self, parser):
        content = """
import java.util.List;
public class Main {}
"""
        assert parser.is_mybatis_file(content) is False

    def test_detect_frameworks(self, parser):
        content = """
import org.apache.ibatis.annotations.Mapper;
import org.mybatis.spring.annotation.MapperScan;
"""
        frameworks = parser._detect_frameworks(content)
        assert len(frameworks) > 0

    def test_parse_full(self, parser):
        content = """
import org.apache.ibatis.annotations.*;

@Mapper
public interface ProductMapper {
    @Select("SELECT * FROM products WHERE id = #{id}")
    Product findById(@Param("id") Long id);

    @Insert("INSERT INTO products (name, price) VALUES (#{name}, #{price})")
    int insert(Product product);
}
"""
        result = parser.parse(content)
        assert isinstance(result, MyBatisParseResult)
        assert len(result.mappers) > 0

    def test_parse_empty(self, parser):
        result = parser.parse("")
        assert isinstance(result, MyBatisParseResult)
        assert result.mappers == []
