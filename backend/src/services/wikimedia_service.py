import asyncio
import json
from html import unescape
from typing import Any, Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup
from flask import current_app
from sqlalchemy.exc import IntegrityError
from tenacity import retry, stop_after_attempt, wait_exponential

from agents.rate_limiter import AsyncRateLimiter
from content.models import MediaCandidate, MediaSuggestion
from extensions import db


class WikimediaService:
    """
    Service for interacting with Wikimedia Commons API.
    """

    API_ENDPOINT = current_app.config.get["WIKIMEDIA_API_ENDPOINT"]

    def __init__(self, calls_per_minute: int = 30) -> None:
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = AsyncRateLimiter(calls_per_minute=calls_per_minute)

    async def __aenter__(self) -> "WikimediaService":
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            await self.session.close()

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def search_images(self, query: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Search for images on Wikimedia Commons using a text query.
        E.g., searching "Panama Canal construction" returns a list of metadata dicts.
        """
        await self.rate_limiter.wait_if_needed()

        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": "6",
            "gsrsearch": f"filetype:bitmap|drawing {query}",
            "gsrlimit": limit,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiextmetadatafilter": "License|LicenseUrl|Attribution|Artist|ImageDescription|ObjectName|Title",
        }

        async with self.session.get(self.API_ENDPOINT, params=params) as response:
            await WikimediaService._ensure_ok(response)

            data = await WikimediaService._safe_json(response)
            if "query" not in data or "pages" not in data["query"]:
                return []

            results: List[Dict[str, Any]] = []
            for page in data["query"]["pages"].values():
                metadata = self._extract_image_metadata(page)
                if metadata:
                    results.append(metadata)

            return results

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def search_category(
        self, category: str, limit: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search for images in a specific Commons category.
        """
        # Normalize category name
        category = category.replace("Category:", "")

        # Get list of file titles in this category
        titles = await self._get_category_members(category, limit)
        if not titles:
            return []

        # Fetch metadata for each file title in batches
        return await self._fetch_files_metadata(titles)

    async def process_suggestion(
        self, suggestion_id: int, max_per_query: int = 10
    ) -> List[MediaCandidate]:
        """
        Process a MediaSuggestion by searching all its categories and queries,
        then create MediaCandidate rows in the DB.
        """
        suggestion = db.session.query(MediaSuggestion).get(suggestion_id)
        if not suggestion:
            raise ValueError(f"MediaSuggestion {suggestion_id} not found")

        candidates: List[MediaCandidate] = []

        # Process categories
        for category in suggestion.commons_categories:
            try:
                results = await self.search_category(category, limit=max_per_query)
                new_candidates = await WikimediaService._bulk_create_candidates(
                    suggestion, results
                )
                candidates.extend(new_candidates)
            except Exception as e:
                current_app.logger.error(f"Error processing category '{category}': {e}")

        # Process search queries
        for query in suggestion.search_queries:
            try:
                results = await self.search_images(query, limit=max_per_query)
                new_candidates = await WikimediaService._bulk_create_candidates(
                    suggestion, results
                )
                candidates.extend(new_candidates)
            except Exception as e:
                current_app.logger.error(f"Error processing query '{query}': {e}")

        return candidates

    # noinspection PyArgumentList
    @staticmethod
    async def _bulk_create_candidates(
        suggestion: MediaSuggestion, results: List[Dict[str, Any]]
    ) -> List[MediaCandidate]:
        """
        Convert a list of image metadata dictionaries into MediaCandidate DB rows,
        ignoring duplicates if found.
        """
        candidates: List[MediaCandidate] = []

        for metadata in results:
            try:
                candidate = MediaCandidate(suggestion_id=suggestion.id, **metadata)
                db.session.add(candidate)
                candidates.append(candidate)
            except Exception as e:
                current_app.logger.error(f"Error creating MediaCandidate: {e}")
                continue

        try:
            db.session.commit()
        except IntegrityError as ie:
            db.session.rollback()
            current_app.logger.error(f"Duplicate candidates found, skipping. {ie}")

        return candidates

    async def _get_category_members(self, category: str, limit: int) -> List[str]:
        """
        Get file titles from a Commons category.
        """
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtype": "file",
            "cmtitle": f"Category:{category}",
            "cmlimit": limit,
        }

        async with self.session.get(self.API_ENDPOINT, params=params) as response:
            await WikimediaService._ensure_ok(response)
            data = await WikimediaService._safe_json(response)

            if "query" not in data or "categorymembers" not in data["query"]:
                return []

            return [member["title"] for member in data["query"]["categorymembers"]]

    async def _fetch_files_metadata(
        self, titles: List[str], batch_size: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch metadata for multiple file titles in batches.
        """
        results: List[Dict[str, Any]] = []

        for i in range(0, len(titles), batch_size):
            batch = titles[i : i + batch_size]

            # Respect rate limit
            await self.rate_limiter.wait_if_needed()

            params = {
                "action": "query",
                "format": "json",
                "prop": "imageinfo",
                "titles": "|".join(batch),
                "iiprop": "url|size|mime|extmetadata",
                "iiextmetadatafilter": "License|LicenseUrl|Attribution|Artist|ImageDescription|ObjectName|Title",
            }

            try:
                async with self.session.get(
                    self.API_ENDPOINT, params=params
                ) as response:
                    await WikimediaService._ensure_ok(response)
                    data = await WikimediaService._safe_json(response)

                    if "query" in data and "pages" in data["query"]:
                        for page in data["query"]["pages"].values():
                            metadata = self._extract_image_metadata(page)
                            if metadata:
                                results.append(metadata)

            except Exception as e:
                current_app.logger.error(
                    f"Error fetching file batch {i}-{i + batch_size}: {e}"
                )
                continue

            # Optional small delay between batches
            await asyncio.sleep(1)

        return results

    @staticmethod
    def _extract_image_metadata(page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract standardized image metadata from a 'page' dict in the Commons API response.
        """
        if "imageinfo" not in page:
            return None

        try:
            info = page["imageinfo"][0]
            ext_metadata = info.get("extmetadata", {})

            # Clean HTML from metadata fields
            description = WikimediaService._clean_html_content(
                ext_metadata.get("ImageDescription", {}).get("value")
            )
            author = WikimediaService._clean_html_content(
                ext_metadata.get("Artist", {}).get("value")
            )

            # For the title, prefer ObjectName over the filename
            obj_name = ext_metadata.get("ObjectName", {}).get("value")
            raw_title = obj_name or page["title"].replace("File:", "")
            title = WikimediaService._clean_html_content(raw_title)

            return {
                "commons_id": page["title"],
                "commons_url": info["url"],
                "title": title,
                "description": description,
                "author": author,
                "license": ext_metadata.get("License", {}).get("value"),
                "license_url": ext_metadata.get("LicenseUrl", {}).get("value"),
                "width": info["width"],
                "height": info["height"],
                "mime_type": info["mime"],
                "file_size": info["size"],
            }
        except (KeyError, IndexError) as e:
            current_app.logger.warning(f"Error extracting image metadata: {e}")
            return None

    @staticmethod
    def _clean_html_content(html_content: Optional[str]) -> Optional[str]:
        """
        Strip HTML tags, unescape entities, and normalize whitespace.
        """
        if not html_content:
            return None

        # First unescape HTML entities
        unescaped = unescape(html_content)

        # Extract text with BeautifulSoup
        soup = BeautifulSoup(unescaped, "html.parser")
        text = soup.get_text(separator=" ")
        text = " ".join(text.split())

        return text.strip() or None

    @staticmethod
    async def _ensure_ok(response: aiohttp.ClientResponse) -> None:
        """
        Raise an exception if the HTTP response status is not 2xx.
        """
        if response.status < 200 or response.status >= 300:
            text = await response.text()
            raise ValueError(f"HTTP {response.status} error from Wikimedia: {text}")

    @staticmethod
    async def _safe_json(response: aiohttp.ClientResponse) -> Dict[str, Any]:
        """
        Safely parse JSON from an aiohttp response, handling unexpected structures.
        """
        try:
            return await response.json()
        except (aiohttp.ContentTypeError, json.JSONDecodeError) as e:
            body = await response.text()
            raise ValueError(f"Invalid JSON in Wikimedia response: {e} | Body: {body}")
