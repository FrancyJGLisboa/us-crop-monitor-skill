#!/usr/bin/env python3
"""
NASS API Client

Client for fetching crop condition data from USDA NASS QuickStats API.

Author: Agent Creator
Version: 1.0.0
"""

import os
import sys
import time
import requests
import argparse
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.cache_manager import CacheManager
from utils.rate_limiter import RateLimiter
from utils.validators import (
    validate_commodity, validate_year, validate_week,
    validate_state, validate_api_key, validate_agg_level,
    ValidationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NassApiError(Exception):
    """Base exception for NASS API errors."""
    pass


class AuthenticationError(NassApiError):
    """API key authentication failed."""
    pass


class RateLimitError(NassApiError):
    """Rate limit exceeded."""
    pass


class DataNotFoundError(NassApiError):
    """No data found for parameters."""
    pass


class NassApiClient:
    """
    Client for USDA NASS QuickStats API.

    Features:
    - Automatic rate limiting
    - Response caching
    - Retry logic with exponential backoff
    - Parameter validation
    """

    BASE_URL = "https://quickstats.nass.usda.gov/api"

    def __init__(self, api_key: Optional[str] = None, cache_dir: str = "data/cache"):
        """
        Initialize NASS API client.

        Args:
            api_key: NASS API key (or None to use env var)
            cache_dir: Directory for cache storage
        """
        # Get API key from arg or environment
        self.api_key = api_key or os.environ.get('NASS_API_KEY')
        try:
            self.api_key = validate_api_key(self.api_key)
        except ValidationError as e:
            logger.error(f"API key validation failed: {e}")
            raise AuthenticationError(str(e))

        # Initialize cache and rate limiter
        self.cache = CacheManager(cache_dir)
        self.rate_limiter = RateLimiter(max_requests=15, time_window=60)

        logger.info("NASS API client initialized")

    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Make API request with retry logic.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            max_retries: Maximum number of retries

        Returns:
            JSON response data

        Raises:
            NassApiError: On API error
        """
        url = f"{self.BASE_URL}/{endpoint}"
        params['key'] = self.api_key

        for attempt in range(max_retries):
            # Rate limiting
            self.rate_limiter.acquire()

            try:
                logger.debug(f"Request: {endpoint} (attempt {attempt + 1}/{max_retries})")

                response = requests.get(url, params=params, timeout=30)

                # Check status
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Response: {len(data)} records")
                    return data

                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key")

                elif response.status_code == 429:
                    wait_time = 60
                    logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                elif response.status_code >= 500:
                    # Server error, retry with backoff
                    if attempt < max_retries - 1:
                        backoff = 2 ** attempt
                        logger.warning(
                            f"Server error {response.status_code}, "
                            f"retrying in {backoff}s..."
                        )
                        time.sleep(backoff)
                        continue
                    else:
                        raise NassApiError(
                            f"Server error {response.status_code} after {max_retries} attempts"
                        )

                else:
                    raise NassApiError(
                        f"API error {response.status_code}: {response.text}"
                    )

            except requests.Timeout:
                if attempt < max_retries - 1:
                    logger.warning("Request timeout, retrying...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise NassApiError(f"Request timeout after {max_retries} attempts")

            except requests.RequestException as e:
                raise NassApiError(f"Request failed: {e}")

        raise NassApiError(f"Request failed after {max_retries} attempts")

    def get_crop_conditions(
        self,
        commodity: str,
        year: int,
        week: Optional[int] = None,
        state: Optional[str] = None,
        agg_level: str = 'NATIONAL',
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get crop condition data.

        Args:
            commodity: Crop name (CORN, SOYBEANS, WHEAT)
            year: Year
            week: Week number (None for all weeks)
            state: State code or name (None for all states)
            agg_level: Aggregation level (NATIONAL, STATE)
            use_cache: Whether to use cache

        Returns:
            List of condition records

        Raises:
            ValidationError: On invalid parameters
            NassApiError: On API error
        """
        # Validate parameters
        commodity = validate_commodity(commodity)
        year = validate_year(year)
        if week is not None:
            week = validate_week(week)
        if state is not None:
            state = validate_state(state)
        agg_level = validate_agg_level(agg_level)

        # Build cache key params
        cache_params = {
            'commodity_desc': commodity,
            'year': year,
            'statisticcat_desc': 'CONDITION',
            'agg_level_desc': agg_level
        }

        if week is not None:
            cache_params['reference_period_desc'] = f'WEEK #{week:02d}'

        if state is not None:
            cache_params['state_alpha' if len(state) == 2 else 'state_name'] = state

        # Check cache (with metadata)
        if use_cache:
            cached_result = self.cache.get_with_metadata(cache_params)
            if cached_result is not None:
                logger.info(f"Cache hit for {commodity} {year} week {week}")
                # Add from_cache flag to data for transparency
                return cached_result['data']

        # Build API params
        api_params = {
            'source_desc': 'SURVEY',
            'sector_desc': 'CROPS',
            'commodity_desc': commodity,
            'statisticcat_desc': 'CONDITION',
            'agg_level_desc': agg_level,
            'year': year,
            'freq_desc': 'WEEKLY'
        }

        if week is not None:
            api_params['reference_period_desc'] = f'WEEK #{week:02d}'

        if state is not None:
            if len(state) == 2:
                api_params['state_alpha'] = state
            else:
                api_params['state_name'] = state

        # Make request
        logger.info(f"Fetching {commodity} {year} week {week} from API...")
        response_data = self._make_request('api_GET', api_params)

        # Check for data
        if 'data' in response_data:
            data = response_data['data']
        else:
            data = response_data

        if not data or len(data) == 0:
            raise DataNotFoundError(
                f"No data found for {commodity} {year} week {week} {state or ''}"
            )

        # Cache the result
        if use_cache:
            self.cache.set(cache_params, data)
            logger.info(f"Cached {len(data)} records")

        return data

    def get_crop_conditions_with_metadata(
        self,
        commodity: str,
        year: int,
        week: Optional[int] = None,
        state: Optional[str] = None,
        agg_level: str = 'NATIONAL',
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get crop condition data WITH metadata.

        Args:
            commodity: Crop name (CORN, SOYBEANS, WHEAT)
            year: Year
            week: Week number (None for all weeks)
            state: State code or name (None for all states)
            agg_level: Aggregation level (NATIONAL, STATE)
            use_cache: Whether to use cache

        Returns:
            Dict with 'data' and 'metadata' keys

        Raises:
            ValidationError: On invalid parameters
            NassApiError: On API error
        """
        from datetime import datetime

        # Validate parameters (same as regular method)
        commodity = validate_commodity(commodity)
        year = validate_year(year)
        if week is not None:
            week = validate_week(week)
        if state is not None:
            state = validate_state(state)
        agg_level = validate_agg_level(agg_level)

        # Build cache key params
        cache_params = {
            'commodity_desc': commodity,
            'year': year,
            'statisticcat_desc': 'CONDITION',
            'agg_level_desc': agg_level
        }

        if week is not None:
            cache_params['reference_period_desc'] = f'WEEK #{week:02d}'

        if state is not None:
            cache_params['state_alpha' if len(state) == 2 else 'state_name'] = state

        # Check cache WITH metadata
        if use_cache:
            cached_result = self.cache.get_with_metadata(cache_params)
            if cached_result is not None:
                logger.info(f"Cache hit for {commodity} {year} week {week}")
                return cached_result

        # Not in cache, fetch from API
        # Build API params
        api_params = {
            'source_desc': 'SURVEY',
            'sector_desc': 'CROPS',
            'commodity_desc': commodity,
            'statisticcat_desc': 'CONDITION',
            'agg_level_desc': agg_level,
            'year': year,
            'freq_desc': 'WEEKLY'
        }

        if week is not None:
            api_params['reference_period_desc'] = f'WEEK #{week:02d}'

        if state is not None:
            if len(state) == 2:
                api_params['state_alpha'] = state
            else:
                api_params['state_name'] = state

        # Make request
        fetched_at = datetime.now()
        logger.info(f"Fetching {commodity} {year} week {week} from API...")
        response_data = self._make_request('api_GET', api_params)

        # Check for data
        if 'data' in response_data:
            data = response_data['data']
        else:
            data = response_data

        if not data or len(data) == 0:
            raise DataNotFoundError(
                f"No data found for {commodity} {year} week {week} {state or ''}"
            )

        # Extract publication date from first record (if available)
        published_at = None
        if data and isinstance(data, list) and len(data) > 0:
            load_time = data[0].get('load_time')
            if load_time:
                try:
                    from datetime import datetime as dt
                    published_at = dt.fromisoformat(load_time.replace('Z', '+00:00'))
                except Exception:
                    pass

        # Create metadata
        metadata = {
            'from_cache': False,
            'fetched_at': fetched_at.isoformat(),
            'published_at': published_at.isoformat() if published_at else None,
            'commodity': commodity,
            'year': year,
            'week': week,
            'metric_type': 'CONDITION',
            'version': '2.0.0'
        }

        # Cache the result
        if use_cache:
            self.cache.set(cache_params, data)
            logger.info(f"Cached {len(data)} records")

        return {
            'data': data,
            'metadata': metadata
        }

    def get_latest_week(
        self,
        commodity: str,
        year: int
    ) -> Optional[int]:
        """
        Get the latest week number available for a commodity/year.

        Args:
            commodity: Crop name
            year: Year

        Returns:
            Latest week number or None if no data
        """
        try:
            # Fetch all weeks for year
            data = self.get_crop_conditions(
                commodity=commodity,
                year=year,
                agg_level='NATIONAL'
            )

            # Extract week numbers
            weeks = set()
            for record in data:
                ref_period = record.get('reference_period_desc', '')
                if 'WEEK' in ref_period:
                    try:
                        week_num = int(ref_period.split('#')[1])
                        weeks.add(week_num)
                    except (IndexError, ValueError):
                        continue

            if weeks:
                return max(weeks)
            else:
                return None

        except (DataNotFoundError, NassApiError) as e:
            logger.warning(f"Could not get latest week: {e}")
            return None

    def get_param_values(self, param_name: str) -> List[str]:
        """
        Get possible values for a parameter.

        Args:
            param_name: Parameter name

        Returns:
            List of possible values
        """
        response = self._make_request(
            'get_param_values',
            {'param': param_name}
        )

        if isinstance(response, dict) and param_name in response:
            return response[param_name]
        elif isinstance(response, list):
            return response
        else:
            return []

    def get_counts(self, params: Dict[str, Any]) -> int:
        """
        Get count of records for parameters.

        Args:
            params: Query parameters

        Returns:
            Count of records
        """
        response = self._make_request('get_counts', params)

        if isinstance(response, dict) and 'count' in response:
            return int(response['count'])
        else:
            return 0

    def get_crop_progress(
        self,
        commodity: str,
        year: int,
        week: Optional[int] = None,
        state: Optional[str] = None,
        agg_level: str = 'NATIONAL',
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get crop progress data (planting, emergence, harvest progress).

        Args:
            commodity: Crop name (CORN, SOYBEANS, WHEAT)
            year: Year
            week: Week number (None for all weeks)
            state: State code or name (None for all states)
            agg_level: Aggregation level (NATIONAL, STATE)
            use_cache: Whether to use cache

        Returns:
            Dict with 'data' and 'metadata' keys

        Raises:
            ValidationError: On invalid parameters
            NassApiError: On API error
        """
        from datetime import datetime

        # Validate parameters
        commodity = validate_commodity(commodity)
        year = validate_year(year)
        if week is not None:
            week = validate_week(week)
        if state is not None:
            state = validate_state(state)
        agg_level = validate_agg_level(agg_level)

        # Build cache key params
        cache_params = {
            'commodity_desc': commodity,
            'year': year,
            'statisticcat_desc': 'PROGRESS',
            'agg_level_desc': agg_level
        }

        if week is not None:
            cache_params['reference_period_desc'] = f'WEEK #{week:02d}'

        if state is not None:
            cache_params['state_alpha' if len(state) == 2 else 'state_name'] = state

        # Check cache
        if use_cache:
            cached_result = self.cache.get_with_metadata(cache_params)
            if cached_result is not None:
                logger.info(f"Cache hit for {commodity} PROGRESS {year} week {week}")
                return cached_result

        # Build API params
        api_params = {
            'source_desc': 'SURVEY',
            'sector_desc': 'CROPS',
            'commodity_desc': commodity,
            'statisticcat_desc': 'PROGRESS',
            'agg_level_desc': agg_level,
            'year': year,
            'freq_desc': 'WEEKLY'
        }

        if week is not None:
            api_params['reference_period_desc'] = f'WEEK #{week:02d}'

        if state is not None:
            if len(state) == 2:
                api_params['state_alpha'] = state
            else:
                api_params['state_name'] = state

        # Make request
        fetched_at = datetime.now()
        logger.info(f"Fetching {commodity} PROGRESS {year} week {week} from API...")
        response_data = self._make_request('api_GET', api_params)

        # Check for data
        if 'data' in response_data:
            data = response_data['data']
        else:
            data = response_data

        if not data or len(data) == 0:
            raise DataNotFoundError(
                f"No progress data found for {commodity} {year} week {week} {state or ''}"
            )

        # Extract publication date from first record
        published_at = None
        if data and isinstance(data, list) and len(data) > 0:
            load_time = data[0].get('load_time')
            if load_time:
                try:
                    from datetime import datetime as dt
                    published_at = dt.fromisoformat(load_time.replace('Z', '+00:00'))
                except Exception:
                    pass

        # Create metadata
        metadata = {
            'from_cache': False,
            'fetched_at': fetched_at.isoformat(),
            'published_at': published_at.isoformat() if published_at else None,
            'commodity': commodity,
            'year': year,
            'week': week,
            'metric_type': 'PROGRESS',
            'version': '2.0.0'
        }

        # Cache the result
        if use_cache:
            self.cache.set(cache_params, data)
            logger.info(f"Cached {len(data)} progress records")

        return {
            'data': data,
            'metadata': metadata
        }

    def get_crop_yield(
        self,
        commodity: str,
        year: int,
        state: Optional[str] = None,
        agg_level: str = 'NATIONAL',
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get crop yield data (bushels per acre).

        Args:
            commodity: Crop name (CORN, SOYBEANS, WHEAT)
            year: Year
            state: State code or name (None for all states)
            agg_level: Aggregation level (NATIONAL, STATE)
            use_cache: Whether to use cache

        Returns:
            Dict with 'data' and 'metadata' keys

        Raises:
            ValidationError: On invalid parameters
            NassApiError: On API error
        """
        from datetime import datetime

        # Validate parameters
        commodity = validate_commodity(commodity)
        year = validate_year(year)
        if state is not None:
            state = validate_state(state)
        agg_level = validate_agg_level(agg_level)

        # Build cache key params
        cache_params = {
            'commodity_desc': commodity,
            'year': year,
            'statisticcat_desc': 'YIELD',
            'agg_level_desc': agg_level
        }

        if state is not None:
            cache_params['state_alpha' if len(state) == 2 else 'state_name'] = state

        # Check cache
        if use_cache:
            cached_result = self.cache.get_with_metadata(cache_params)
            if cached_result is not None:
                logger.info(f"Cache hit for {commodity} YIELD {year}")
                return cached_result

        # Build API params
        api_params = {
            'source_desc': 'SURVEY',
            'sector_desc': 'CROPS',
            'commodity_desc': commodity,
            'statisticcat_desc': 'YIELD',
            'agg_level_desc': agg_level,
            'year': year
        }

        if state is not None:
            if len(state) == 2:
                api_params['state_alpha'] = state
            else:
                api_params['state_name'] = state

        # Make request
        fetched_at = datetime.now()
        logger.info(f"Fetching {commodity} YIELD {year} from API...")
        response_data = self._make_request('api_GET', api_params)

        # Check for data
        if 'data' in response_data:
            data = response_data['data']
        else:
            data = response_data

        if not data or len(data) == 0:
            raise DataNotFoundError(
                f"No yield data found for {commodity} {year} {state or ''}"
            )

        # Extract publication date
        published_at = None
        if data and isinstance(data, list) and len(data) > 0:
            load_time = data[0].get('load_time')
            if load_time:
                try:
                    from datetime import datetime as dt
                    published_at = dt.fromisoformat(load_time.replace('Z', '+00:00'))
                except Exception:
                    pass

        # Create metadata
        metadata = {
            'from_cache': False,
            'fetched_at': fetched_at.isoformat(),
            'published_at': published_at.isoformat() if published_at else None,
            'commodity': commodity,
            'year': year,
            'metric_type': 'YIELD',
            'version': '2.0.0'
        }

        # Cache the result
        if use_cache:
            self.cache.set(cache_params, data)
            logger.info(f"Cached {len(data)} yield records")

        return {
            'data': data,
            'metadata': metadata
        }

    def get_crop_production(
        self,
        commodity: str,
        year: int,
        state: Optional[str] = None,
        agg_level: str = 'NATIONAL',
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get crop production data (total production in bushels).

        Args:
            commodity: Crop name (CORN, SOYBEANS, WHEAT)
            year: Year
            state: State code or name (None for all states)
            agg_level: Aggregation level (NATIONAL, STATE)
            use_cache: Whether to use cache

        Returns:
            Dict with 'data' and 'metadata' keys

        Raises:
            ValidationError: On invalid parameters
            NassApiError: On API error
        """
        from datetime import datetime

        # Validate parameters
        commodity = validate_commodity(commodity)
        year = validate_year(year)
        if state is not None:
            state = validate_state(state)
        agg_level = validate_agg_level(agg_level)

        # Build cache key params
        cache_params = {
            'commodity_desc': commodity,
            'year': year,
            'statisticcat_desc': 'PRODUCTION',
            'agg_level_desc': agg_level
        }

        if state is not None:
            cache_params['state_alpha' if len(state) == 2 else 'state_name'] = state

        # Check cache
        if use_cache:
            cached_result = self.cache.get_with_metadata(cache_params)
            if cached_result is not None:
                logger.info(f"Cache hit for {commodity} PRODUCTION {year}")
                return cached_result

        # Build API params
        api_params = {
            'source_desc': 'SURVEY',
            'sector_desc': 'CROPS',
            'commodity_desc': commodity,
            'statisticcat_desc': 'PRODUCTION',
            'agg_level_desc': agg_level,
            'year': year
        }

        if state is not None:
            if len(state) == 2:
                api_params['state_alpha'] = state
            else:
                api_params['state_name'] = state

        # Make request
        fetched_at = datetime.now()
        logger.info(f"Fetching {commodity} PRODUCTION {year} from API...")
        response_data = self._make_request('api_GET', api_params)

        # Check for data
        if 'data' in response_data:
            data = response_data['data']
        else:
            data = response_data

        if not data or len(data) == 0:
            raise DataNotFoundError(
                f"No production data found for {commodity} {year} {state or ''}"
            )

        # Extract publication date
        published_at = None
        if data and isinstance(data, list) and len(data) > 0:
            load_time = data[0].get('load_time')
            if load_time:
                try:
                    from datetime import datetime as dt
                    published_at = dt.fromisoformat(load_time.replace('Z', '+00:00'))
                except Exception:
                    pass

        # Create metadata
        metadata = {
            'from_cache': False,
            'fetched_at': fetched_at.isoformat(),
            'published_at': published_at.isoformat() if published_at else None,
            'commodity': commodity,
            'year': year,
            'metric_type': 'PRODUCTION',
            'version': '2.0.0'
        }

        # Cache the result
        if use_cache:
            self.cache.set(cache_params, data)
            logger.info(f"Cached {len(data)} production records")

        return {
            'data': data,
            'metadata': metadata
        }

    def get_crop_area(
        self,
        commodity: str,
        year: int,
        area_type: str = 'PLANTED',
        state: Optional[str] = None,
        agg_level: str = 'NATIONAL',
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Get crop area data (acres planted or harvested).

        Args:
            commodity: Crop name (CORN, SOYBEANS, WHEAT)
            year: Year
            area_type: 'PLANTED' or 'HARVESTED'
            state: State code or name (None for all states)
            agg_level: Aggregation level (NATIONAL, STATE)
            use_cache: Whether to use cache

        Returns:
            Dict with 'data' and 'metadata' keys

        Raises:
            ValidationError: On invalid parameters
            NassApiError: On API error
        """
        from datetime import datetime

        # Validate parameters
        commodity = validate_commodity(commodity)
        year = validate_year(year)
        if state is not None:
            state = validate_state(state)
        agg_level = validate_agg_level(agg_level)

        # Validate area_type
        area_type = area_type.upper()
        if area_type not in ['PLANTED', 'HARVESTED']:
            raise ValidationError(f"Invalid area_type: {area_type}. Must be PLANTED or HARVESTED")

        statisticcat = f'AREA {area_type}'

        # Build cache key params
        cache_params = {
            'commodity_desc': commodity,
            'year': year,
            'statisticcat_desc': statisticcat,
            'agg_level_desc': agg_level
        }

        if state is not None:
            cache_params['state_alpha' if len(state) == 2 else 'state_name'] = state

        # Check cache
        if use_cache:
            cached_result = self.cache.get_with_metadata(cache_params)
            if cached_result is not None:
                logger.info(f"Cache hit for {commodity} {statisticcat} {year}")
                return cached_result

        # Build API params
        api_params = {
            'source_desc': 'SURVEY',
            'sector_desc': 'CROPS',
            'commodity_desc': commodity,
            'statisticcat_desc': statisticcat,
            'agg_level_desc': agg_level,
            'year': year
        }

        if state is not None:
            if len(state) == 2:
                api_params['state_alpha'] = state
            else:
                api_params['state_name'] = state

        # Make request
        fetched_at = datetime.now()
        logger.info(f"Fetching {commodity} {statisticcat} {year} from API...")
        response_data = self._make_request('api_GET', api_params)

        # Check for data
        if 'data' in response_data:
            data = response_data['data']
        else:
            data = response_data

        if not data or len(data) == 0:
            raise DataNotFoundError(
                f"No area data found for {commodity} {year} {state or ''}"
            )

        # Extract publication date
        published_at = None
        if data and isinstance(data, list) and len(data) > 0:
            load_time = data[0].get('load_time')
            if load_time:
                try:
                    from datetime import datetime as dt
                    published_at = dt.fromisoformat(load_time.replace('Z', '+00:00'))
                except Exception:
                    pass

        # Create metadata
        metadata = {
            'from_cache': False,
            'fetched_at': fetched_at.isoformat(),
            'published_at': published_at.isoformat() if published_at else None,
            'commodity': commodity,
            'year': year,
            'metric_type': statisticcat,
            'version': '2.0.0'
        }

        # Cache the result
        if use_cache:
            self.cache.set(cache_params, data)
            logger.info(f"Cached {len(data)} area records")

        return {
            'data': data,
            'metadata': metadata
        }

    def get_crop_data(
        self,
        metric_type: str,
        commodity: str,
        year: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Unified method to get crop data of any type.

        Routes to the appropriate specialized method based on metric_type.

        Args:
            metric_type: Type of metric ('CONDITION', 'PROGRESS', 'YIELD', 'PRODUCTION', 'AREA PLANTED', 'AREA HARVESTED')
            commodity: Crop name (CORN, SOYBEANS, WHEAT)
            year: Year
            **kwargs: Additional arguments passed to specific method

        Returns:
            Dict with 'data' and 'metadata' keys

        Raises:
            ValidationError: On invalid parameters
            NassApiError: On API error
        """
        metric_type = metric_type.upper()

        if metric_type == 'CONDITION':
            return self.get_crop_conditions_with_metadata(commodity, year, **kwargs)
        elif metric_type == 'PROGRESS':
            return self.get_crop_progress(commodity, year, **kwargs)
        elif metric_type == 'YIELD':
            return self.get_crop_yield(commodity, year, **kwargs)
        elif metric_type == 'PRODUCTION':
            return self.get_crop_production(commodity, year, **kwargs)
        elif metric_type in ['AREA PLANTED', 'PLANTED']:
            return self.get_crop_area(commodity, year, area_type='PLANTED', **kwargs)
        elif metric_type in ['AREA HARVESTED', 'HARVESTED']:
            return self.get_crop_area(commodity, year, area_type='HARVESTED', **kwargs)
        else:
            raise ValidationError(
                f"Invalid metric_type: {metric_type}. "
                f"Must be one of: CONDITION, PROGRESS, YIELD, PRODUCTION, AREA PLANTED, AREA HARVESTED"
            )


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Fetch crop condition data from NASS API'
    )
    parser.add_argument(
        '--commodity',
        required=True,
        choices=['CORN', 'SOYBEANS', 'WHEAT'],
        help='Crop commodity'
    )
    parser.add_argument(
        '--year',
        type=int,
        required=True,
        help='Year'
    )
    parser.add_argument(
        '--week',
        type=int,
        help='Week number (omit for all weeks)'
    )
    parser.add_argument(
        '--state',
        help='State code (e.g., IA) or name'
    )
    parser.add_argument(
        '--agg-level',
        default='NATIONAL',
        choices=['NATIONAL', 'STATE'],
        help='Aggregation level'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable cache'
    )
    parser.add_argument(
        '--prefetch',
        action='store_true',
        help='Prefetch all states for current week'
    )

    args = parser.parse_args()

    # Initialize client
    try:
        client = NassApiClient()
    except AuthenticationError as e:
        print(f"Error: {e}")
        print("\nSet your NASS API key:")
        print("  export NASS_API_KEY='your_key_here'")
        print("\nGet a free key at: https://quickstats.nass.usda.gov/api/")
        sys.exit(1)

    # Fetch data
    try:
        if args.prefetch:
            print(f"Prefetching {args.commodity} {args.year}...")
            # Get latest week
            latest_week = client.get_latest_week(args.commodity, args.year)
            if latest_week:
                print(f"Latest week: {latest_week}")
                # Fetch national and all states
                data = client.get_crop_conditions(
                    commodity=args.commodity,
                    year=args.year,
                    week=latest_week,
                    agg_level='STATE',
                    use_cache=not args.no_cache
                )
                print(f"Prefetched {len(data)} records")
            else:
                print("No data available yet")
        else:
            data = client.get_crop_conditions(
                commodity=args.commodity,
                year=args.year,
                week=args.week,
                state=args.state,
                agg_level=args.agg_level,
                use_cache=not args.no_cache
            )

            print(f"\nFetched {len(data)} records for:")
            print(f"  Commodity: {args.commodity}")
            print(f"  Year: {args.year}")
            print(f"  Week: {args.week or 'ALL'}")
            print(f"  State: {args.state or 'ALL'}")
            print(f"  Level: {args.agg_level}")

            # Show sample
            if data:
                print(f"\nSample record:")
                sample = data[0]
                for key in ['commodity_desc', 'year', 'reference_period_desc',
                           'week_ending', 'state_name', 'short_desc', 'Value']:
                    if key in sample:
                        print(f"  {key}: {sample[key]}")

    except (ValidationError, DataNotFoundError, NassApiError) as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
