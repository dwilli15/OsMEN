#!/usr/bin/env python3
"""
OsMEN Media Entertainment Integration

Provides:
- TMDB API for movie/TV metadata
- OpenSubtitles for subtitle search/download
- DVD Authoring pipeline (future)

Usage:
    from integrations.media_entertainment import MediaIntegration

    media = MediaIntegration()

    # Search movies
    movies = await media.search_movies("Inception")

    # Get subtitles
    subs = await media.search_subtitles(imdb_id="tt1375666", language="en")
"""

import asyncio
import hashlib
import json
import logging
import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import aiohttp

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================


@dataclass
class MediaConfig:
    """Media integration configuration"""

    # TMDB settings
    tmdb_api_key: Optional[str] = None
    tmdb_base_url: str = "https://api.themoviedb.org/3"
    tmdb_image_base: str = "https://image.tmdb.org/t/p"

    # OpenSubtitles settings
    opensub_api_key: Optional[str] = None
    opensub_base_url: str = "https://api.opensubtitles.com/api/v1"
    opensub_user_agent: str = "OsMEN v1.0"

    @classmethod
    def from_env(cls) -> "MediaConfig":
        """Load config from environment"""
        return cls(
            tmdb_api_key=os.getenv("TMDB_API_KEY"),
            opensub_api_key=os.getenv("OPENSUBTITLES_API_KEY"),
        )


# ============================================================================
# TMDB Integration
# ============================================================================


class TMDBClient:
    """The Movie Database API client"""

    def __init__(self, config: MediaConfig):
        self.config = config
        self.api_key = config.tmdb_api_key
        self.base_url = config.tmdb_base_url
        self.available = bool(self.api_key)

        if not self.available:
            logger.warning("TMDB_API_KEY not set - TMDB integration disabled")

    async def _request(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make API request"""
        if not self.available:
            return {"error": "TMDB not configured"}

        url = f"{self.base_url}{endpoint}"
        params = params or {}
        params["api_key"] = self.api_key

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {
                        "error": f"TMDB API error: {response.status}",
                        "message": await response.text(),
                    }

    async def search_movies(
        self, query: str, year: Optional[int] = None, page: int = 1
    ) -> Dict[str, Any]:
        """Search for movies"""
        params = {"query": query, "page": page}
        if year:
            params["year"] = year

        return await self._request("/search/movie", params)

    async def search_tv(
        self, query: str, first_air_year: Optional[int] = None, page: int = 1
    ) -> Dict[str, Any]:
        """Search for TV shows"""
        params = {"query": query, "page": page}
        if first_air_year:
            params["first_air_date_year"] = first_air_year

        return await self._request("/search/tv", params)

    async def get_movie(self, movie_id: int) -> Dict[str, Any]:
        """Get movie details"""
        return await self._request(
            f"/movie/{movie_id}",
            {"append_to_response": "credits,videos,images,similar"},
        )

    async def get_tv(self, tv_id: int) -> Dict[str, Any]:
        """Get TV show details"""
        return await self._request(
            f"/tv/{tv_id}", {"append_to_response": "credits,videos,images,similar"}
        )

    async def get_tv_season(self, tv_id: int, season: int) -> Dict[str, Any]:
        """Get TV season details"""
        return await self._request(f"/tv/{tv_id}/season/{season}")

    async def get_movie_by_imdb(self, imdb_id: str) -> Dict[str, Any]:
        """Find movie by IMDB ID"""
        result = await self._request(f"/find/{imdb_id}", {"external_source": "imdb_id"})

        if "movie_results" in result and result["movie_results"]:
            movie = result["movie_results"][0]
            return await self.get_movie(movie["id"])

        return {"error": "Movie not found"}

    async def get_trending(
        self,
        media_type: str = "movie",  # movie, tv, all
        time_window: str = "week",  # day, week
    ) -> Dict[str, Any]:
        """Get trending content"""
        return await self._request(f"/trending/{media_type}/{time_window}")

    async def get_popular_movies(self, page: int = 1) -> Dict[str, Any]:
        """Get popular movies"""
        return await self._request("/movie/popular", {"page": page})

    async def get_popular_tv(self, page: int = 1) -> Dict[str, Any]:
        """Get popular TV shows"""
        return await self._request("/tv/popular", {"page": page})

    def get_image_url(
        self,
        path: str,
        size: str = "w500",  # w92, w154, w185, w342, w500, w780, original
    ) -> str:
        """Get full image URL"""
        if not path:
            return ""
        return f"{self.config.tmdb_image_base}/{size}{path}"


# ============================================================================
# OpenSubtitles Integration
# ============================================================================


class OpenSubtitlesClient:
    """OpenSubtitles API client"""

    def __init__(self, config: MediaConfig):
        self.config = config
        self.api_key = config.opensub_api_key
        self.base_url = config.opensub_base_url
        self.available = bool(self.api_key)
        self.token: Optional[str] = None

        if not self.available:
            logger.warning("OPENSUBTITLES_API_KEY not set - subtitles disabled")

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request"""
        if not self.available:
            return {"error": "OpenSubtitles not configured"}

        url = f"{self.base_url}{endpoint}"

        headers = {
            "Api-Key": self.api_key,
            "User-Agent": self.config.opensub_user_agent,
            "Content-Type": "application/json",
        }

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, headers=headers, params=params) as response:
                    return await self._handle_response(response)
            elif method == "POST":
                async with session.post(url, headers=headers, json=data) as response:
                    return await self._handle_response(response)

        return {"error": "Invalid method"}

    async def _handle_response(self, response) -> Dict[str, Any]:
        """Handle API response"""
        if response.status in (200, 201):
            return await response.json()
        else:
            return {
                "error": f"OpenSubtitles API error: {response.status}",
                "message": await response.text(),
            }

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login to get token (optional, for higher limits)"""
        result = await self._request(
            "POST", "/login", {"username": username, "password": password}
        )

        if "token" in result:
            self.token = result["token"]

        return result

    async def search_subtitles(
        self,
        query: Optional[str] = None,
        imdb_id: Optional[str] = None,
        tmdb_id: Optional[int] = None,
        languages: Optional[List[str]] = None,
        season_number: Optional[int] = None,
        episode_number: Optional[int] = None,
        moviehash: Optional[str] = None,
        page: int = 1,
    ) -> Dict[str, Any]:
        """Search for subtitles"""
        params = {"page": page}

        if query:
            params["query"] = query
        if imdb_id:
            # Remove 'tt' prefix if present
            params["imdb_id"] = imdb_id.replace("tt", "")
        if tmdb_id:
            params["tmdb_id"] = tmdb_id
        if languages:
            params["languages"] = ",".join(languages)
        if season_number is not None:
            params["season_number"] = season_number
        if episode_number is not None:
            params["episode_number"] = episode_number
        if moviehash:
            params["moviehash"] = moviehash

        return await self._request("GET", "/subtitles", params=params)

    async def download_subtitle(
        self, file_id: int, output_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """Download a subtitle file"""
        # Get download link
        result = await self._request("POST", "/download", {"file_id": file_id})

        if "link" not in result:
            return {"error": "Could not get download link", "details": result}

        # Download the file
        async with aiohttp.ClientSession() as session:
            async with session.get(result["link"]) as response:
                if response.status == 200:
                    content = await response.read()

                    with open(output_path, "wb") as f:
                        f.write(content)

                    return {
                        "success": True,
                        "output_path": str(output_path),
                        "remaining": result.get("remaining"),
                    }
                else:
                    return {"error": f"Download failed: {response.status}"}

    @staticmethod
    def compute_hash(file_path: Union[str, Path]) -> str:
        """Compute OpenSubtitles hash for a video file"""
        file_size = os.path.getsize(file_path)
        hash_value = file_size

        with open(file_path, "rb") as f:
            # Read first 64KB
            for _ in range(65536 // 8):
                buffer = f.read(8)
                if len(buffer) == 8:
                    hash_value += struct.unpack("q", buffer)[0]
                    hash_value &= 0xFFFFFFFFFFFFFFFF

            # Read last 64KB
            f.seek(max(0, file_size - 65536))
            for _ in range(65536 // 8):
                buffer = f.read(8)
                if len(buffer) == 8:
                    hash_value += struct.unpack("q", buffer)[0]
                    hash_value &= 0xFFFFFFFFFFFFFFFF

        return f"{hash_value:016x}"


# ============================================================================
# Unified Media Integration
# ============================================================================


class MediaIntegration:
    """Unified media integration"""

    def __init__(self, config: Optional[MediaConfig] = None):
        self.config = config or MediaConfig.from_env()
        self.tmdb = TMDBClient(self.config)
        self.subtitles = OpenSubtitlesClient(self.config)

    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            "tmdb": {
                "available": self.tmdb.available,
                "configured": bool(self.config.tmdb_api_key),
            },
            "opensubtitles": {
                "available": self.subtitles.available,
                "configured": bool(self.config.opensub_api_key),
                "authenticated": bool(self.subtitles.token),
            },
        }

    # TMDB shortcuts
    async def search_movies(self, query: str, **kwargs) -> Dict[str, Any]:
        return await self.tmdb.search_movies(query, **kwargs)

    async def search_tv(self, query: str, **kwargs) -> Dict[str, Any]:
        return await self.tmdb.search_tv(query, **kwargs)

    async def get_movie(self, movie_id: int) -> Dict[str, Any]:
        return await self.tmdb.get_movie(movie_id)

    async def get_tv(self, tv_id: int) -> Dict[str, Any]:
        return await self.tmdb.get_tv(tv_id)

    async def get_trending(self, **kwargs) -> Dict[str, Any]:
        return await self.tmdb.get_trending(**kwargs)

    # Subtitle shortcuts
    async def search_subtitles(self, **kwargs) -> Dict[str, Any]:
        return await self.subtitles.search_subtitles(**kwargs)

    async def download_subtitle(self, file_id: int, output_path: str) -> Dict[str, Any]:
        return await self.subtitles.download_subtitle(file_id, output_path)

    # Combined operations
    async def get_movie_with_subtitles(
        self, imdb_id: str, languages: List[str] = ["en"]
    ) -> Dict[str, Any]:
        """Get movie info with available subtitles"""
        movie = await self.tmdb.get_movie_by_imdb(imdb_id)

        if "error" in movie:
            return movie

        subtitles = await self.subtitles.search_subtitles(
            imdb_id=imdb_id, languages=languages
        )

        return {"movie": movie, "subtitles": subtitles.get("data", [])}


# ============================================================================
# MCP Tool Handlers
# ============================================================================

_media: Optional[MediaIntegration] = None


def get_media() -> MediaIntegration:
    """Get or create media integration"""
    global _media
    if _media is None:
        _media = MediaIntegration()
    return _media


async def handle_search_movies(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for movie search"""
    media = get_media()

    query = params.get("query")
    if not query:
        return {"error": "query required"}

    return await media.search_movies(
        query, year=params.get("year"), page=params.get("page", 1)
    )


async def handle_search_tv(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for TV search"""
    media = get_media()

    query = params.get("query")
    if not query:
        return {"error": "query required"}

    return await media.search_tv(
        query, first_air_year=params.get("year"), page=params.get("page", 1)
    )


async def handle_get_movie(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for movie details"""
    media = get_media()

    movie_id = params.get("movie_id") or params.get("id")
    imdb_id = params.get("imdb_id")

    if imdb_id:
        return await media.tmdb.get_movie_by_imdb(imdb_id)
    elif movie_id:
        return await media.get_movie(int(movie_id))
    else:
        return {"error": "movie_id or imdb_id required"}


async def handle_search_subtitles(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for subtitle search"""
    media = get_media()

    return await media.search_subtitles(
        query=params.get("query"),
        imdb_id=params.get("imdb_id"),
        tmdb_id=params.get("tmdb_id"),
        languages=params.get("languages", ["en"]),
        season_number=params.get("season"),
        episode_number=params.get("episode"),
    )


async def handle_download_subtitle(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for subtitle download"""
    media = get_media()

    file_id = params.get("file_id")
    output_path = params.get("output_path")

    if not file_id:
        return {"error": "file_id required"}
    if not output_path:
        return {"error": "output_path required"}

    return await media.download_subtitle(int(file_id), output_path)


async def handle_media_status(params: Dict[str, Any]) -> Dict[str, Any]:
    """MCP handler for media status"""
    media = get_media()
    return media.get_status()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":

    async def main():
        media = MediaIntegration()
        print("Media Integration Status:")
        print(json.dumps(media.get_status(), indent=2))

        # Test TMDB if available
        if media.tmdb.available:
            print("\nSearching TMDB for 'Inception'...")
            results = await media.search_movies("Inception")
            if "results" in results:
                for movie in results["results"][:3]:
                    print(
                        f"  - {movie['title']} ({movie.get('release_date', 'N/A')[:4]})"
                    )

    asyncio.run(main())
