"""
Tests for AutoMapper Enhanced Parser.

Tests profile extraction, CreateMap detection, resolvers, converters, projections.
Part of CodeTrellis v4.96 (Session 76)
"""

import pytest
from codetrellis.automapper_parser_enhanced import EnhancedAutoMapperParser, AutoMapperParseResult


# ── Fixtures ─────────────────────────────────────────────

SAMPLE_PROFILE = '''
using AutoMapper;

public class ProductMappingProfile : Profile
{
    public ProductMappingProfile()
    {
        CreateMap<Product, ProductDto>()
            .ForMember(dest => dest.FullName, opt => opt.MapFrom(src => src.Name))
            .ForMember(dest => dest.CategoryName, opt => opt.MapFrom(src => src.Category.Name))
            .ReverseMap();

        CreateMap<CreateProductCommand, Product>()
            .ForMember(dest => dest.CreatedAt, opt => opt.Ignore());

        CreateMap<Order, OrderDto>()
            .ForMember(dest => dest.Total, opt => opt.Condition(src => src.Total > 0));
    }
}
'''

SAMPLE_RESOLVER = '''
using AutoMapper;

public class TaxValueResolver : IValueResolver<Order, OrderDto, decimal>
{
    private readonly ITaxService _taxService;

    public TaxValueResolver(ITaxService taxService) => _taxService = taxService;

    public decimal Resolve(Order source, OrderDto dest, decimal destMember, ResolutionContext ctx)
    {
        return _taxService.Calculate(source.SubTotal);
    }
}
'''

SAMPLE_CONVERTER = '''
using AutoMapper;

public class MoneyToDecimalConverter : ITypeConverter<Money, decimal>
{
    public decimal Convert(Money source, decimal dest, ResolutionContext ctx)
    {
        return source.Amount;
    }
}
'''

SAMPLE_PROJECTION = '''
using AutoMapper.QueryableExtensions;

public class ProductService
{
    private readonly IMapper _mapper;
    private readonly AppDbContext _ctx;

    public async Task<List<ProductDto>> GetAllAsync()
    {
        return await _ctx.Products
            .ProjectTo<ProductDto>(_mapper.ConfigurationProvider)
            .ToListAsync();
    }
}
'''


# ── Tests ────────────────────────────────────────────────

class TestEnhancedAutoMapperParser:
    """Tests for EnhancedAutoMapperParser."""

    def setup_method(self):
        self.parser = EnhancedAutoMapperParser()

    def test_is_automapper_file_profile(self):
        assert self.parser.is_automapper_file(SAMPLE_PROFILE)

    def test_is_automapper_file_resolver(self):
        assert self.parser.is_automapper_file(SAMPLE_RESOLVER)

    def test_is_automapper_file_negative(self):
        assert not self.parser.is_automapper_file("class Foo { }")
        assert not self.parser.is_automapper_file("")

    def test_parse_profile(self):
        result = self.parser.parse(SAMPLE_PROFILE, "Mappings/ProductMappingProfile.cs")
        assert isinstance(result, AutoMapperParseResult)
        assert len(result.profiles) >= 1
        assert result.total_profiles >= 1
        assert result.total_mappings >= 2  # Product→ProductDto, CreateProductCommand→Product, Order→OrderDto

    def test_parse_reverse_map(self):
        result = self.parser.parse(SAMPLE_PROFILE, "Mappings/ProductMappingProfile.cs")
        # At least one mapping should have reverse_map
        profile = result.profiles[0] if result.profiles else {}
        assert profile.get('total_mappings', 0) >= 2

    def test_parse_value_resolver(self):
        result = self.parser.parse(SAMPLE_RESOLVER, "Resolvers/TaxValueResolver.cs")
        assert len(result.value_resolvers) >= 1
        resolver = result.value_resolvers[0]
        assert resolver.get('name') == 'TaxValueResolver'

    def test_parse_type_converter(self):
        result = self.parser.parse(SAMPLE_CONVERTER, "Converters/MoneyConverter.cs")
        assert len(result.type_converters) >= 1
        converter = result.type_converters[0]
        assert converter.get('name') == 'MoneyToDecimalConverter'

    def test_parse_projection(self):
        result = self.parser.parse(SAMPLE_PROJECTION, "Services/ProductService.cs")
        assert len(result.projections) >= 1

    def test_framework_detection(self):
        result = self.parser.parse(SAMPLE_PROFILE, "test.cs")
        assert len(result.detected_frameworks) > 0

    def test_file_classification(self):
        result = self.parser.parse(SAMPLE_PROFILE, "Mappings/ProductProfile.cs")
        assert result.file_type == "profile"

        result2 = self.parser.parse(SAMPLE_RESOLVER, "Resolvers/Tax.cs")
        assert result2.file_type == "resolver"

    def test_empty_input(self):
        result = self.parser.parse("", "test.cs")
        assert len(result.profiles) == 0
        assert result.total_mappings == 0
