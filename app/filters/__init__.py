"""Sistema de Filtros"""

from app.filters.base import Filter, FilterStats, FilterChain
from app.filters.sum_range import SumRangeFilter
from app.filters.even_odd import EvenOddFilter
from app.filters.consecutive import ConsecutiveFilter
from app.filters.quadrants import QuadrantsFilter
from app.filters.repeat_last import RepeatLastFilter
from app.filters.popular_patterns import PopularPatternsFilter

__all__ = [
    "Filter",
    "FilterStats",
    "FilterChain",
    "SumRangeFilter",
    "EvenOddFilter",
    "ConsecutiveFilter",
    "QuadrantsFilter",
    "RepeatLastFilter",
    "PopularPatternsFilter",
]
