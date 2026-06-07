"""Unit tests for ecnyss.util.stats module."""
import math
from ecnyss.util.stats import (
    mean,
    median,
    variance,
    stdev,
    percentile,
    quantile,
    min_max,
    sum,
    count,
)


class TestMean:
    """Tests for mean function."""
    
    def test_empty_raises(self):
        """Empty sequence raises ValueError."""
        try:
            mean([])
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
    
    def test_single_value(self):
        """Single value returns itself."""
        assert mean([5.0]) == 5.0
    
    def test_multiple_values(self):
        """Multiple values calculates correct mean."""
        assert mean([1.0, 2.0, 3.0, 4.0, 5.0]) == 3.0
    
    def test_negative_values(self):
        """Negative values handled correctly."""
        assert mean([-1.0, 0.0, 1.0]) == 0.0
    
    def test_floats(self):
        """Float values handled correctly."""
        result = mean([1.5, 2.5, 3.5])
        assert abs(result - 2.5) < 1e-10


class TestMedian:
    """Tests for median function."""
    
    def test_odd_length(self):
        """Odd length returns middle value."""
        assert median([1.0, 2.0, 3.0, 4.0, 5.0]) == 3.0
    
    def test_even_length(self):
        """Even length returns average of two middle values."""
        assert median([1.0, 2.0, 3.0, 4.0]) == 2.5
    
    def test_unsorted_input(self):
        """Unsorted input handled correctly."""
        assert median([5.0, 1.0, 3.0, 2.0, 4.0]) == 3.0
    
    def test_single_value(self):
        """Single value returns itself."""
        assert median([7.0]) == 7.0
    
    def test_empty_raises(self):
        """Empty sequence raises ValueError."""
        try:
            median([])
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestVariance:
    """Tests for variance function."""
    
    def test_population_variance(self):
        """Population variance (ddof=0)."""
        # [1, 2, 3, 4, 5] mean=3, variance = ((1-3)^2 + (2-3)^2 + (3-3)^2 + (4-3)^2 + (5-3)^2) / 5 = 10/5 = 2
        assert variance([1.0, 2.0, 3.0, 4.0, 5.0], ddof=0) == 2.0
    
    def test_sample_variance(self):
        """Sample variance (ddof=1)."""
        # [1, 2, 3, 4, 5] mean=3, variance = 10/4 = 2.5
        assert variance([1.0, 2.0, 3.0, 4.0, 5.0], ddof=1) == 2.5
    
    def test_known_values(self):
        """Test with known variance values."""
        # All same values should have variance 0
        assert variance([5.0, 5.0, 5.0, 5.0], ddof=0) == 0.0
    
    def test_empty_raises(self):
        """Empty sequence raises ValueError."""
        try:
            variance([], ddof=0)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestStdev:
    """Tests for stdev function."""
    
    def test_sqrt_of_variance(self):
        """Standard deviation is sqrt of variance."""
        var = variance([1.0, 2.0, 3.0, 4.0, 5.0], ddof=0)
        std = stdev([1.0, 2.0, 3.0, 4.0, 5.0], ddof=0)
        assert abs(std - math.sqrt(var)) < 1e-10
    
    def test_empty_raises(self):
        """Empty sequence raises ValueError."""
        try:
            stdev([], ddof=0)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestPercentile:
    """Tests for percentile function."""
    
    def test_0th_percentile(self):
        """0th percentile returns minimum."""
        assert percentile([1.0, 2.0, 3.0, 4.0, 5.0], 0) == 1.0
    
    def test_50th_percentile(self):
        """50th percentile equals median."""
        assert percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50) == median([1.0, 2.0, 3.0, 4.0, 5.0])
    
    def test_100th_percentile(self):
        """100th percentile returns maximum."""
        assert percentile([1.0, 2.0, 3.0, 4.0, 5.0], 100) == 5.0
    
    def test_interpolation(self):
        """Interpolation between values."""
        # 25th percentile of [1, 2, 3, 4] should be 1.75 with linear interpolation
        result = percentile([1.0, 2.0, 3.0, 4.0], 25)
        assert abs(result - 1.75) < 1e-10
    
    def test_bounds_checking(self):
        """Percentile out of bounds raises ValueError."""
        try:
            percentile([1.0, 2.0, 3.0], -1)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        
        try:
            percentile([1.0, 2.0, 3.0], 101)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestQuantile:
    """Tests for quantile function."""
    
    def test_0_0_quantile(self):
        """0.0 quantile returns minimum."""
        assert quantile([1.0, 2.0, 3.0, 4.0, 5.0], 0.0) == 1.0
    
    def test_0_5_quantile(self):
        """0.5 quantile equals median."""
        assert quantile([1.0, 2.0, 3.0, 4.0, 5.0], 0.5) == median([1.0, 2.0, 3.0, 4.0, 5.0])
    
    def test_1_0_quantile(self):
        """1.0 quantile returns maximum."""
        assert quantile([1.0, 2.0, 3.0, 4.0, 5.0], 1.0) == 5.0
    
    def test_bounds_checking(self):
        """Quantile out of bounds raises ValueError."""
        try:
            quantile([1.0, 2.0, 3.0], -0.1)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        
        try:
            quantile([1.0, 2.0, 3.0], 1.1)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestMinMax:
    """Tests for min_max function."""
    
    def test_returns_tuple(self):
        """Returns (min, max) tuple."""
        result = min_max([1.0, 2.0, 3.0, 4.0, 5.0])
        assert result == (1.0, 5.0)
    
    def test_single_value(self):
        """Single value returns (value, value)."""
        assert min_max([7.0]) == (7.0, 7.0)
    
    def test_empty_raises(self):
        """Empty sequence raises ValueError."""
        try:
            min_max([])
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestSum:
    """Tests for sum function."""
    
    def test_basic(self):
        """Basic sum calculation."""
        assert sum([1.0, 2.0, 3.0, 4.0, 5.0]) == 15.0
    
    def test_empty(self):
        """Empty sequence returns 0."""
        assert sum([]) == 0.0


class TestCount:
    """Tests for count function."""
    
    def test_basic(self):
        """Basic count."""
        assert count([1.0, 2.0, 3.0, 4.0, 5.0]) == 5
    
    def test_empty(self):
        """Empty sequence returns 0."""
        assert count([]) == 0
    
    def test_single_value(self):
        """Single value returns 1."""
        assert count([7.0]) == 1
